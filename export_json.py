import json
import os
import math

def generate_synthetic_data():
    frames = []
    
    # 600 frames total (3 phases: 0-200 Nominal, 200-400 Comm Loss + Disturbance, 400-600 AI Recovery)
    num_steps = 600
    
    radius = 9.0
    orbit_speed = 0.5
    phase_angles = {1: 0.0, 2: 0.5, 3: -0.5}

    for step in range(num_steps):
        time_sec = step * 0.1
        
        mode = "BASELINE" if step < 400 else "AI-ASSISTED"
        
        if step < 200:
            event = "NOMINAL"
        elif step < 300:
            event = "DISTURBANCE BURST"
        elif step < 400:
            event = "LEADER CRITICAL FAULT"
        elif step < 450:
            event = "REASSIGNMENT IN PROGRESS"
        else:
            event = "AI MITIGATING DISTURBANCE"
            
        satellites = []
        links = []
        
        for sat_id in [1, 2, 3]:
            # Orbit math
            angle = orbit_speed * time_sec + phase_angles[sat_id]
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = 0.0
            
            # Roles over time: At step 400, Backup (3) becomes Leader, Leader (1) becomes Follower (degraded)
            if step < 400:
                roles = {1: "leader", 2: "follower", 3: "backup"}
            else:
                roles = {1: "follower", 2: "follower", 3: "leader"}
                
            role = roles[sat_id]
            health = "healthy"
            
            # Wobble / pointing error
            pointing_error = 0.0
            
            if step >= 200 and step < 400: # Disturbance
                pointing_error = math.sin(step) * 20.0 # big wobble
                
            if step >= 400: # AI active
                pointing_error = math.sin(step) * 2.0 # tiny wobble
                
            # Leader degraded
            if sat_id == 1 and step >= 300: # Permanent fault
                health = "failed"
                if step < 400:
                    pointing_error += 30.0 # huge wobble before reassignment
                    z += math.sin(step) * 2.0 # physically shaking
                    
            satellites.append({
                "id": f"sat{sat_id}",
                "role": role,
                "position": [x, y, z],
                "pointingError": pointing_error,
                "health": health
            })
            
        # Add Links (Leader connects to others)
        # Find leader
        leader_id = None
        for s in satellites:
            if s["role"] == "leader":
                leader_id = s["id"]
                
        if leader_id:
            for s in satellites:
                target_id = s["id"]
                if target_id != leader_id:
                    # Link status
                    status = "healthy"
                    if step >= 200 and step < 400 and s["id"] != "sat1":
                        # Simulate packet drops during disturbance
                        import random
                        if random.random() < 0.2:
                            status = "lost"
                            
                    links.append({
                        "source": leader_id,
                        "target": target_id,
                        "status": status
                    })
                    
        frames.append({
            "time": time_sec,
            "mode": mode,
            "event": event,
            "satellites": satellites,
            "links": links
        })

    json_path = os.path.join("web-demo", "src", "demoData.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(frames, f)
        
    print(f"Exported {len(frames)} synthetic frames to {json_path}")

if __name__ == "__main__":
    generate_synthetic_data()
