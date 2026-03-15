# ============================================================
# BLOODBRIDGE — EXTENSION MODULE
# All new features built ON TOP of existing project code.
# Paste each cell AFTER your existing notebook cells.
# DO NOT modify any existing code.
# ============================================================

# ─────────────────────────────────────────────────────────────
# CELL 1 — Install new dependencies
# ─────────────────────────────────────────────────────────────
# !pip install -q gtts pydub ipyleaflet ipywidgets folium requests

# ─────────────────────────────────────────────────────────────
# CELL 2 — Cross-Type Blood Compatibility Engine
# ─────────────────────────────────────────────────────────────

BLOOD_COMPATIBILITY = {
    "A+":  {"can_receive": ["A+", "A-", "O+", "O-"], "can_donate_to": ["A+", "AB+"]},
    "A-":  {"can_receive": ["A-", "O-"],              "can_donate_to": ["A+", "A-", "AB+", "AB-"]},
    "B+":  {"can_receive": ["B+", "B-", "O+", "O-"], "can_donate_to": ["B+", "AB+"]},
    "B-":  {"can_receive": ["B-", "O-"],              "can_donate_to": ["B+", "B-", "AB+", "AB-"]},
    "AB+": {"can_receive": ["A+","A-","B+","B-","AB+","AB-","O+","O-"], "can_donate_to": ["AB+"]},
    "AB-": {"can_receive": ["A-","B-","AB-","O-"],    "can_donate_to": ["AB+", "AB-"]},
    "O+":  {"can_receive": ["O+", "O-"],              "can_donate_to": ["A+","B+","AB+","O+"]},
    "O-":  {"can_receive": ["O-"],                    "can_donate_to": ["A+","A-","B+","B-","AB+","AB-","O+","O-"]},
}

COMPATIBILITY_REASONS = {
    "O-":  "O- is the universal donor — no A, B, or Rh antigens, accepted by all blood types.",
    "O+":  "O+ has no A or B antigens; the Rh+ factor is tolerated by Rh+ recipients.",
    "AB+": "AB+ is the universal recipient — carries all antigens, so any blood is compatible.",
    "A-":  "A- matches A+ patients when Rh+ blood isn't available (Rh-negative is safe for Rh+ recipients).",
    "B-":  "B- is Rh-negative, safe for B+ recipients in emergencies.",
    "AB-": "AB- can donate to all Rh- types; useful when exact match unavailable.",
}

def explain_compatibility(donor_bg, patient_bg):
    """Return human-readable explanation of why a cross-type match is safe."""
    compat = BLOOD_COMPATIBILITY.get(donor_bg, {})
    if patient_bg in compat.get("can_donate_to", []):
        reason = COMPATIBILITY_REASONS.get(donor_bg, f"{donor_bg} is compatible with {patient_bg} per ABO/Rh rules.")
        return True, reason
    return False, f"{donor_bg} is NOT compatible with {patient_bg}."

def recommend_donors_crosstype(patient, max_results=5, max_distance_km=50):
    """
    Enhanced donor recommendation with cross-type compatibility.
    Falls back to compatible blood groups if exact match pool is exhausted.
    Builds on existing recommend_donors() logic — does NOT replace it.
    """
    from geopy.distance import geodesic

    donors_ref = db.collection("donors").stream()
    exact_matches = []
    cross_matches = []

    for d in donors_ref:
        donor = d.to_dict()
        donor["Donor_ID"] = d.id

        if not (
            (donor.get("Eligibility_Final") == "Eligible" or donor.get("Eligibility") == "Eligible")
            and donor.get("Availability")
        ):
            continue

        donor_bg = donor.get("Blood_Group", "")
        patient_bg = patient["Blood_Group"]
        donor_loc = (donor["Latitude"], donor["Longitude"])
        patient_loc = (patient["Latitude"], patient["Longitude"])
        distance = geodesic(donor_loc, patient_loc).km

        if distance > max_distance_km:
            continue

        donor["Distance_km"] = round(distance, 2)

        if donor_bg == patient_bg:
            donor["Match_Type"] = "EXACT"
            donor["Compatibility_Note"] = "Same blood group — ideal match."
            exact_matches.append(donor)
        else:
            is_compat, reason = explain_compatibility(donor_bg, patient_bg)
            if is_compat:
                donor["Match_Type"] = "CROSS_TYPE"
                donor["Compatibility_Note"] = reason
                cross_matches.append(donor)

    exact_matches = sorted(exact_matches, key=lambda x: x["Distance_km"])
    cross_matches = sorted(cross_matches, key=lambda x: x["Distance_km"])

    # Prefer exact; pad with cross-type if needed
    combined = exact_matches + cross_matches
    combined = combined[:max_results]

    print(f"\n🔗 Found {len(exact_matches)} exact + {len(cross_matches)} cross-type compatible donors:")
    for m in combined:
        tag = "✅ EXACT" if m["Match_Type"] == "EXACT" else "🔄 CROSS"
        print(f"  {tag} | {m['Full_Name']} ({m['Blood_Group']}) — {m['Distance_km']} km")
        print(f"        ℹ️  {m['Compatibility_Note']}")

    return combined


# ─────────────────────────────────────────────────────────────
# CELL 3 — Hospital EHR Simulator
# ─────────────────────────────────────────────────────────────

import random
from datetime import datetime, timedelta

EHR_DIAGNOSES = [
    "Acute Anaemia", "Thalassaemia", "Sickle Cell Crisis",
    "Post-Operative Haemorrhage", "Trauma - RTA", "Obstetric Emergency",
    "Haematological Malignancy", "Dengue with Thrombocytopenia",
    "Chronic Kidney Disease", "GI Bleed"
]

EHR_WARDS = ["ICU", "Emergency", "Surgical Ward", "Maternity", "Oncology", "General Ward"]

def simulate_hospital_ehr(patient_id=None):
    """
    Simulate a hospital EHR record for a patient.
    If patient_id is given, attaches to existing patient in Firestore.
    Otherwise creates a standalone EHR record.
    """
    ehr = {
        "EHR_ID": f"EHR{random.randint(10000, 99999)}",
        "Patient_ID": patient_id or f"PAT{random.randint(1000,9999)}",
        "Admission_Date": (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat(),
        "Ward": random.choice(EHR_WARDS),
        "Diagnosis": random.choice(EHR_DIAGNOSES),
        "Attending_Physician": random.choice([
            "Dr. Priya Suresh", "Dr. Karthik Rajan", "Dr. Meenakshi Iyer",
            "Dr. Arun Balaji", "Dr. Kavitha Nair"
        ]),
        "Haemoglobin_g_dL": round(random.uniform(4.5, 11.5), 1),
        "Platelet_count_lakh": round(random.uniform(0.5, 4.5), 2),
        "Blood_Pressure": f"{random.randint(90,140)}/{random.randint(60,90)}",
        "Transfusion_Required": True,
        "Units_Ordered": random.randint(1, 4),
        "Blood_Group_Required": random.choice(list(BLOOD_COMPATIBILITY.keys())),
        "Crossmatch_Done": random.choice([True, False]),
        "Consent_Obtained": True,
        "Notes": "Auto-generated EHR simulation record for BloodBridge integration.",
        "Created_At": datetime.now().isoformat(),
    }

    # Determine urgency from Hb
    if ehr["Haemoglobin_g_dL"] < 6.0:
        ehr["Clinical_Urgency"] = "High"
    elif ehr["Haemoglobin_g_dL"] < 8.5:
        ehr["Clinical_Urgency"] = "Medium"
    else:
        ehr["Clinical_Urgency"] = "Low"

    db.collection("ehr_records").document(ehr["EHR_ID"]).set(ehr)

    print(f"\n🏥 EHR RECORD GENERATED")
    print(f"   EHR ID      : {ehr['EHR_ID']}")
    print(f"   Patient     : {ehr['Patient_ID']}")
    print(f"   Diagnosis   : {ehr['Diagnosis']}")
    print(f"   Ward        : {ehr['Ward']}")
    print(f"   Hb          : {ehr['Haemoglobin_g_dL']} g/dL")
    print(f"   Urgency     : {ehr['Clinical_Urgency']}")
    print(f"   Units Needed: {ehr['Units_Ordered']} x {ehr['Blood_Group_Required']}")
    print(f"   Physician   : {ehr['Attending_Physician']}")

    return ehr

def get_ehr_for_patient(patient_id):
    """Fetch latest EHR for a patient from Firestore."""
    records = db.collection("ehr_records")\
        .where("Patient_ID", "==", patient_id)\
        .stream()
    results = [r.to_dict() for r in records]
    if results:
        latest = sorted(results, key=lambda x: x["Created_At"], reverse=True)[0]
        print(f"\n📋 Latest EHR: {latest['EHR_ID']} | {latest['Diagnosis']} | Urgency: {latest['Clinical_Urgency']}")
        return latest
    print("No EHR found for this patient.")
    return None


# ─────────────────────────────────────────────────────────────
# CELL 4 — Blood Unit Inventory Tracker
# ─────────────────────────────────────────────────────────────

def get_inventory_status(request_id):
    """Live inventory breakdown for a donation request."""
    doc = db.collection("donation_requests").document(request_id).get().to_dict()
    if not doc:
        return {}

    units_needed = doc.get("Units", 1)
    status = doc.get("Status", "REQUESTED")

    reserved = 1 if status in ["ACCEPTED", "ON_THE_WAY", "ARRIVED", "DONATED"] else 0
    en_route  = 1 if status in ["ON_THE_WAY"] else 0
    collected = 1 if status in ["DONATED"] else 0
    pending   = max(units_needed - reserved, 0)

    inventory = {
        "Request_ID": request_id,
        "Units_Required": units_needed,
        "Reserved": reserved,
        "En_Route": en_route,
        "Collected": collected,
        "Pending": pending,
        "Status": status,
    }

    print(f"\n🩸 INVENTORY — Request {request_id}")
    print(f"   Required : {units_needed}")
    print(f"   Reserved : {reserved}")
    print(f"   En Route : {en_route}")
    print(f"   Collected: {collected}")
    print(f"   Pending  : {pending}")

    return inventory


# ─────────────────────────────────────────────────────────────
# CELL 5 — Gratitude Wall
# ─────────────────────────────────────────────────────────────

def post_gratitude(request_id, patient_id, message):
    """Patient posts anonymous thank-you after donation."""
    entry = {
        "Request_ID": request_id,
        "Patient_ID": patient_id,
        "Message": message,
        "Timestamp": datetime.now().isoformat(),
        "Anonymous": True,
    }
    ref = db.collection("gratitude_wall").add(entry)
    print(f"\n💌 Gratitude posted! (ID: {ref[1].id})")
    print(f"   Message: \"{message}\"")
    return ref[1].id

def get_gratitude_wall(limit=10):
    """Fetch recent messages from the gratitude wall."""
    docs = db.collection("gratitude_wall").stream()
    messages = [d.to_dict() for d in docs]
    messages = sorted(messages, key=lambda x: x["Timestamp"], reverse=True)[:limit]
    print(f"\n💌 GRATITUDE WALL (last {len(messages)} messages)")
    for i, m in enumerate(messages, 1):
        print(f"   {i}. \"{m['Message']}\" — {m['Timestamp'][:10]}")
    return messages


# ─────────────────────────────────────────────────────────────
# CELL 6 — Family/Caregiver Alert System
# ─────────────────────────────────────────────────────────────

def register_caregiver(patient_id, caregiver_name, caregiver_phone, caregiver_email=""):
    """Register a caregiver to receive stage alerts for a patient."""
    caregiver = {
        "Patient_ID": patient_id,
        "Caregiver_Name": caregiver_name,
        "Caregiver_Phone": caregiver_phone,
        "Caregiver_Email": caregiver_email,
        "Registered_At": datetime.now().isoformat(),
    }
    db.collection("patients").document(patient_id).update({
        "Caregiver": caregiver
    })
    print(f"\n👨‍👩‍👧 Caregiver '{caregiver_name}' registered for patient {patient_id}.")
    return caregiver

def send_caregiver_alert(patient_id, stage):
    """
    Simulate sending a caregiver push notification at each stage.
    In production, replace print with Twilio SMS / FCM push.
    Stages: DONOR_MATCHED | DONOR_EN_ROUTE | DONOR_ARRIVED | DONATION_COMPLETE
    """
    doc = db.collection("patients").document(patient_id).get().to_dict()
    caregiver = doc.get("Caregiver", {})
    if not caregiver:
        return

    stage_messages = {
        "DONOR_MATCHED":   "✅ A donor has been matched for your family member's blood request.",
        "DONOR_EN_ROUTE":  "🚗 The donor is now on the way to the hospital.",
        "DONOR_ARRIVED":   "🏥 The donor has arrived at the hospital.",
        "DONATION_COMPLETE":"🩸 Blood donation has been successfully completed. Thank you!",
    }

    message = stage_messages.get(stage, f"Update: {stage}")
    print(f"\n📲 CAREGIVER ALERT → {caregiver.get('Caregiver_Name')} ({caregiver.get('Caregiver_Phone')})")
    print(f"   {message}")

    db.collection("caregiver_alerts").add({
        "Patient_ID": patient_id,
        "Stage": stage,
        "Message": message,
        "Sent_At": datetime.now().isoformat(),
        "Caregiver": caregiver,
    })


# ─────────────────────────────────────────────────────────────
# CELL 7 — Donor Cooldown Tracker (56-day rule)
# ─────────────────────────────────────────────────────────────

def check_donor_cooldown(donor_id):
    """
    Check if a donor has completed the mandatory 56-day rest period.
    Reads last donation timestamp from Firestore.
    """
    doc = db.collection("donors").document(donor_id).get().to_dict()
    last_donation_str = doc.get("Last_Donation_Date")

    if not last_donation_str:
        print(f"\n✅ Donor {donor_id} — No previous donation found. Eligible immediately.")
        return True, 0

    last_donation = datetime.fromisoformat(last_donation_str)
    days_since = (datetime.now() - last_donation).days
    days_remaining = max(56 - days_since, 0)

    if days_remaining == 0:
        print(f"\n✅ Donor {donor_id} — Cooldown complete ({days_since} days since last donation). Eligible!")
        return True, 0
    else:
        eligible_date = last_donation + timedelta(days=56)
        print(f"\n⏳ Donor {donor_id} — {days_remaining} days remaining. Eligible from {eligible_date.date()}.")
        return False, days_remaining

def mark_donation_complete_with_cooldown(donor_id, request_id):
    """
    Mark donation done AND stamp Last_Donation_Date for cooldown tracking.
    Call AFTER complete_donation_qr().
    """
    now = datetime.now().isoformat()
    db.collection("donors").document(donor_id).update({
        "Last_Donation_Date": now,
        "Donations_Count": firestore.Increment(1),
    })
    db.collection("donation_requests").document(request_id).update({
        "Donation_Completed": True,
        "Donation_Timestamp": now,
    })
    print(f"\n🗓️ Cooldown timer started for donor {donor_id}. Next eligible: {(datetime.now() + timedelta(days=56)).date()}")


# ─────────────────────────────────────────────────────────────
# CELL 8 — Personal Health Trend (Donor vitals history chart)
# ─────────────────────────────────────────────────────────────

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_donor_health_trends(donor_id):
    """
    Pull all post-donation vitals from Firestore for this donor and plot trends.
    Reads from post_donation_vitals sub-collection (written by extended recording below).
    """
    docs = db.collection("post_donation_vitals")\
        .where("Donor_ID", "==", donor_id)\
        .stream()

    records = [d.to_dict() for d in docs]

    if len(records) < 2:
        print("📊 Not enough donation history to plot trends. At least 2 donations needed.")
        return

    records = sorted(records, key=lambda x: x["Timestamp"])
    dates   = [datetime.fromisoformat(r["Timestamp"]) for r in records]
    bp_vals = [r.get("Post_Donation_BP", 0) for r in records]
    hb_vals = [r.get("Post_Donation_Hb", 0) for r in records]
    pulse_vals = [r.get("Post_Donation_Pulse", 0) for r in records]

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    fig.suptitle(f"Donor {donor_id} — Health Trend Across Donations", fontsize=14, fontweight="bold")

    axes[0].plot(dates, bp_vals, marker="o", color="#e74c3c", linewidth=2)
    axes[0].set_ylabel("BP Systolic (mmHg)")
    axes[0].axhline(120, color="gray", linestyle="--", alpha=0.5, label="Normal")
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(dates, hb_vals, marker="s", color="#2980b9", linewidth=2)
    axes[1].set_ylabel("Haemoglobin (g/dL)")
    axes[1].axhline(12.5, color="gray", linestyle="--", alpha=0.5, label="Min safe")
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    axes[2].plot(dates, pulse_vals, marker="^", color="#27ae60", linewidth=2)
    axes[2].set_ylabel("Pulse (bpm)")
    axes[2].axhline(72, color="gray", linestyle="--", alpha=0.5, label="Resting avg")
    axes[2].legend(); axes[2].grid(True, alpha=0.3)

    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()

def record_post_donation_vitals_extended(donor_id, bp, pulse, hb, dizziness):
    """
    Extended version of post_donation_risk_assessment — additionally writes to
    post_donation_vitals collection for trend tracking.
    Call this AFTER your existing post_donation_risk_assessment().
    """
    entry = {
        "Donor_ID": donor_id,
        "Post_Donation_BP": bp,
        "Post_Donation_Pulse": pulse,
        "Post_Donation_Hb": hb,
        "Vasovagal_Symptoms": dizziness,
        "Timestamp": datetime.now().isoformat(),
    }
    db.collection("post_donation_vitals").add(entry)
    print(f"📈 Vitals recorded for trend tracking → donor {donor_id}")


# ─────────────────────────────────────────────────────────────
# CELL 9 — Pre-Donation Anxiety Coach (Guided Breathing + TTS)
# ─────────────────────────────────────────────────────────────

import time as _time

def guided_breathing_exercise(cycles=4):
    """
    Text-based 4-7-8 breathing coach triggered when HIGH_STRESS detected.
    In Colab, each step prints with a timed pause.
    TTS (gTTS) is used if available.
    """
    print("\n🧘 PRE-DONATION ANXIETY COACH")
    print("High stress detected. Let's do a 4-7-8 breathing exercise before we re-assess.\n")

    try:
        from gtts import gTTS
        from IPython.display import Audio, display
        import io

        def speak(text):
            tts = gTTS(text=text, lang="en", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            display(Audio(fp.read(), autoplay=True))
    except Exception:
        def speak(text):
            print(f"🔊 {text}")

    for cycle in range(1, cycles + 1):
        print(f"\n--- Cycle {cycle} of {cycles} ---")
        speak("Breathe in for 4 seconds")
        print("  🟢 Breathe IN  (4s)"); _time.sleep(4)
        speak("Hold for 7 seconds")
        print("  🟡 HOLD        (7s)"); _time.sleep(7)
        speak("Breathe out for 8 seconds")
        print("  🔵 Breathe OUT (8s)"); _time.sleep(8)

    print("\n✅ Exercise complete. Let's re-check your stress level.")

def pre_donation_stress_gate(donor_id, free_text):
    """
    Drop-in replacement for the stress check block in register_donor().
    Uses your existing detect_stress(). If HIGH_STRESS, runs breathing coach
    and re-evaluates before deferring.
    """
    stress_level, stress_prob = detect_stress(free_text)
    print(f"\n🧠 Stress Level: {stress_level} (score: {stress_prob:.2f})")

    if stress_level == "HIGH_STRESS":
        guided_breathing_exercise(cycles=3)
        re_text = input("\nHow are you feeling NOW after the exercise? ")
        stress_level, stress_prob = detect_stress(re_text)
        print(f"🧠 Re-assessed Stress Level: {stress_level} (score: {stress_prob:.2f})")

    return stress_level, stress_prob


# ─────────────────────────────────────────────────────────────
# CELL 10 — Nearby Blood Camp Radar
# ─────────────────────────────────────────────────────────────

def register_blood_camp(name, lat, lon, date_str, organizer, contact):
    """Admin: register a blood donation camp in Firestore."""
    camp = {
        "Camp_ID": f"CAMP{random.randint(1000,9999)}",
        "Name": name,
        "Latitude": lat,
        "Longitude": lon,
        "Date": date_str,
        "Organizer": organizer,
        "Contact": contact,
        "Active": True,
        "Created_At": datetime.now().isoformat(),
    }
    db.collection("blood_camps").document(camp["Camp_ID"]).set(camp)
    print(f"\n⛺ Camp '{name}' registered: {camp['Camp_ID']}")
    return camp

def find_nearby_camps(donor_lat, donor_lon, radius_km=5):
    """Find active blood camps within radius_km of donor location."""
    from geopy.distance import geodesic

    camps = db.collection("blood_camps").where("Active", "==", True).stream()
    nearby = []

    for c in camps:
        camp = c.to_dict()
        dist = geodesic((donor_lat, donor_lon), (camp["Latitude"], camp["Longitude"])).km
        if dist <= radius_km:
            camp["Distance_km"] = round(dist, 2)
            nearby.append(camp)

    nearby = sorted(nearby, key=lambda x: x["Distance_km"])

    if nearby:
        print(f"\n📍 {len(nearby)} camp(s) within {radius_km} km:")
        for c in nearby:
            print(f"   ⛺ {c['Name']} — {c['Distance_km']} km | {c['Date']} | Contact: {c['Contact']}")
    else:
        print(f"\n📍 No camps found within {radius_km} km.")

    return nearby


# ─────────────────────────────────────────────────────────────
# CELL 11 — Cross-Region Donor Pooling (uses your forecast model)
# ─────────────────────────────────────────────────────────────

REGION_ADJACENCY = {
    "Coimbatore":  ["Tiruppur", "Erode", "Nilgiris"],
    "Chennai":     ["Kanchipuram", "Tiruvallur", "Chengalpattu"],
    "Madurai":     ["Dindigul", "Virudhunagar", "Theni"],
    "Tiruchirappalli": ["Karur", "Pudukkottai", "Thanjavur"],
    "Salem":       ["Namakkal", "Dharmapuri", "Krishnagiri"],
}

def cross_region_pool(primary_region, blood_group, required_units=2):
    """
    If local donors exhausted, forecast adjacent region demand and
    recommend pre-positioning units from low-demand neighbors.
    Uses your existing forecast_region_bg() and shortage_risk().
    """
    print(f"\n🌐 CROSS-REGION POOLING — {primary_region} needs {required_units}x {blood_group}")

    adjacent = REGION_ADJACENCY.get(primary_region, [])
    if not adjacent:
        print("   No adjacent regions configured.")
        return []

    candidates = []
    for region in adjacent:
        try:
            forecast = forecast_region_bg(region, blood_group, days=1)
            predicted_demand = forecast[0][1] if forecast else 999
            p_shortage, gap, _, stock = shortage_risk(region, blood_group, horizon=1)

            surplus = max(int(stock) - predicted_demand, 0)
            if surplus >= required_units and p_shortage < 0.4:
                candidates.append({
                    "Region": region,
                    "Available_Stock": int(stock),
                    "Predicted_Demand": predicted_demand,
                    "Surplus": surplus,
                    "Shortage_Prob": round(p_shortage, 2),
                })
                print(f"   ✅ {region} — Surplus: {surplus} units | Shortage risk: {p_shortage:.0%}")
            else:
                print(f"   ❌ {region} — Insufficient surplus (stock={int(stock)}, demand≈{predicted_demand})")
        except Exception as e:
            print(f"   ⚠️ {region} — Forecast unavailable: {e}")

    if candidates:
        best = min(candidates, key=lambda x: x["Shortage_Prob"])
        print(f"\n🚚 Recommend pre-positioning from: {best['Region']} ({best['Surplus']} units available)")
    else:
        print("\n⚠️ No suitable adjacent region found. Escalate to state blood bank.")

    return candidates


# ─────────────────────────────────────────────────────────────
# CELL 12 — Train DonorRiskNet on real post-donation Firestore data
# ─────────────────────────────────────────────────────────────

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

def collect_training_data_from_firestore():
    """Pull post_donation_vitals from Firestore and build a training dataset."""
    docs = db.collection("post_donation_vitals").stream()
    records = [d.to_dict() for d in docs]

    if len(records) < 10:
        print(f"⚠️ Only {len(records)} records available. Need at least 10 to train DonorRiskNet.")
        return None, None

    rows = []
    labels = []
    for r in records:
        bp    = r.get("Post_Donation_BP", 120)
        pulse = r.get("Post_Donation_Pulse", 72)
        hb    = r.get("Post_Donation_Hb", 13.0)
        dizzy = r.get("Vasovagal_Symptoms", 0)
        rows.append([bp, pulse, hb, dizzy])

        # Rule-based label from existing logic
        if hb < 11 or bp < 90 or dizzy == 1:
            labels.append(2)  # HIGH_RISK
        elif bp < 100 or pulse > 110:
            labels.append(1)  # OBSERVE
        else:
            labels.append(0)  # SAFE

    X = torch.tensor(rows, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    return X, y

def train_donor_risk_net(epochs=50, batch_size=16, lr=0.001):
    """
    Train your existing DonorRiskNet (defined in original code) on real Firestore data.
    Saves weights to models/donor_risk_net.pt
    """
    print("\n🧬 Training DonorRiskNet on real post-donation data...")
    X, y = collect_training_data_from_firestore()

    if X is None:
        # Generate synthetic bootstrap data if insufficient real data
        print("📊 Generating synthetic bootstrap data (50 samples)...")
        X_raw = []
        y_raw = []
        for _ in range(50):
            bp    = random.randint(85, 145)
            pulse = random.randint(55, 120)
            hb    = round(random.uniform(8.0, 16.5), 1)
            dizzy = random.randint(0, 1)
            X_raw.append([bp, pulse, hb, dizzy])
            if hb < 11 or bp < 90 or dizzy:
                y_raw.append(2)
            elif bp < 100 or pulse > 110:
                y_raw.append(1)
            else:
                y_raw.append(0)
        X = torch.tensor(X_raw, dtype=torch.float32)
        y = torch.tensor(y_raw, dtype=torch.long)

    dataset = TensorDataset(X, y)
    loader  = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Use your existing dri_model (DonorRiskNet instance)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(dri_model.parameters(), lr=lr)

    dri_model.train()
    for epoch in range(epochs):
        total_loss = 0
        for xb, yb in loader:
            optimizer.zero_grad()
            preds = dri_model(xb)
            loss  = criterion(preds, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{epochs} — Loss: {total_loss/len(loader):.4f}")

    import os
    os.makedirs("models", exist_ok=True)
    torch.save(dri_model.state_dict(), "models/donor_risk_net.pt")
    print("\n✅ DonorRiskNet trained and saved to models/donor_risk_net.pt")
    return dri_model

def predict_donor_risk_net(bp, pulse, hb, dizziness):
    """Use trained DonorRiskNet for inference."""
    dri_model.eval()
    x = torch.tensor([[bp, pulse, hb, dizziness]], dtype=torch.float32)
    with torch.no_grad():
        probs = dri_model(x)[0].tolist()
    classes = ["SAFE", "OBSERVE", "HIGH_RISK"]
    pred = classes[probs.index(max(probs))]
    print(f"\n🧠 DonorRiskNet → {pred} | SAFE:{probs[0]:.2f} OBSERVE:{probs[1]:.2f} HIGH_RISK:{probs[2]:.2f}")
    return pred, probs


# ─────────────────────────────────────────────────────────────
# CELL 13 — Gamified Donor Impact Dashboard (terminal version)
# ─────────────────────────────────────────────────────────────

BADGES = [
    (1,  "🩸 First Drop",      "First donation completed."),
    (3,  "🔥 Triple Saver",    "3 donations — you're on fire!"),
    (5,  "⭐ Life Star",        "5 donations — a true hero."),
    (10, "🏅 Platinum Donor",  "10 donations — legendary status."),
    (25, "🦸 SuperDonor",       "25 donations — you're extraordinary."),
]

def get_donor_badges(donation_count):
    earned = [b for b in BADGES if donation_count >= b[0]]
    return earned

def donor_impact_dashboard(donor_id):
    doc = db.collection("donors").document(donor_id).get().to_dict()
    if not doc:
        print("Donor not found.")
        return

    count     = doc.get("Donations_Count", 0)
    lives     = count * 3  # 1 donation can help up to 3 patients
    last_date = doc.get("Last_Donation_Date", "N/A")
    badges    = get_donor_badges(count)

    cooldown_ok, days_left = check_donor_cooldown(donor_id)

    print(f"\n{'='*50}")
    print(f"  🩸 DONOR IMPACT DASHBOARD — {doc.get('Full_Name', donor_id)}")
    print(f"{'='*50}")
    print(f"  Total Donations : {count}")
    print(f"  Lives Impacted  : ~{lives}")
    print(f"  Last Donation   : {last_date[:10] if last_date != 'N/A' else 'N/A'}")
    print(f"  Cooldown Status : {'✅ Ready to donate!' if cooldown_ok else f'⏳ {days_left} days remaining'}")
    print(f"\n  🏆 BADGES EARNED:")
    if badges:
        for b in badges:
            print(f"    {b[1]} — {b[2]}")
    else:
        print("    None yet — make your first donation!")
    print(f"{'='*50}")


# ─────────────────────────────────────────────────────────────
# CELL 14 — Live Donor Map (Folium, renders in Colab)
# ─────────────────────────────────────────────────────────────

def render_donor_map(request_id, patient):
    """
    Render a live Folium map in Colab showing donor location,
    patient/hospital location, and route line.
    Pull last GPS update from Firestore tracking sub-collection.
    """
    try:
        import folium
        from IPython.display import display, HTML
    except ImportError:
        print("Run: !pip install folium")
        return

    hospital_lat = patient["Latitude"]
    hospital_lon = patient["Longitude"]

    # Get latest donor tracking point
    tracking_docs = list(
        db.collection("donation_requests")
          .document(request_id)
          .collection("tracking")
          .stream()
    )

    donor_lat, donor_lon, eta = hospital_lat, hospital_lon, 0
    if tracking_docs:
        latest = sorted(
            [d.to_dict() for d in tracking_docs],
            key=lambda x: str(x.get("Timestamp", "")),
            reverse=True
        )[0]
        donor_lat = latest.get("Current_Lat", hospital_lat)
        donor_lon = latest.get("Current_Lon", hospital_lon)
        eta       = latest.get("ETA_minutes", 0)

    center_lat = (hospital_lat + donor_lat) / 2
    center_lon = (hospital_lon + donor_lon) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13,
                   tiles="CartoDB dark_matter")

    folium.Marker(
        [hospital_lat, hospital_lon],
        popup=f"🏥 Hospital\n{patient['Full_Name']}",
        icon=folium.Icon(color="red", icon="plus-sign", prefix="glyphicon")
    ).add_to(m)

    folium.Marker(
        [donor_lat, donor_lon],
        popup=f"🩸 Donor (ETA: {eta:.0f} min)",
        icon=folium.Icon(color="blue", icon="user", prefix="glyphicon")
    ).add_to(m)

    folium.PolyLine(
        [[donor_lat, donor_lon], [hospital_lat, hospital_lon]],
        color="#e74c3c", weight=3, opacity=0.8, dash_array="10"
    ).add_to(m)

    folium.Circle(
        [hospital_lat, hospital_lon],
        radius=500, color="#e74c3c", fill=True, fill_opacity=0.1
    ).add_to(m)

    map_html = m._repr_html_()
    display(HTML(f"""
    <div style="font-family:monospace;background:#111;color:#e74c3c;padding:8px;border-radius:6px;margin-bottom:6px;">
        🚗 Live Donor Tracking — ETA: {eta:.0f} min | Request: {request_id}
    </div>
    {map_html}
    """))

    return m


# ─────────────────────────────────────────────────────────────
# CELL 15 — Launch Full Frontend UI in Colab
# ─────────────────────────────────────────────────────────────

def launch_frontend_ui():
    """
    Renders the complete BloodBridge UI inside a Colab output cell.
    All interactions call back into the Python functions defined above.
    """
    from IPython.display import display, HTML
    import json as _json

    # Serialize some live data for the UI
    try:
        gratitude = get_gratitude_wall(5)
    except Exception:
        gratitude = []

    gratitude_json = _json.dumps([
        {"message": g.get("Message",""), "date": g.get("Timestamp","")[:10]}
        for g in gratitude
    ])

    html_content = open("/content/bloodbridge_ui.html").read() if False else _get_ui_html(gratitude_json)
    display(HTML(html_content))

def _get_ui_html(gratitude_json="[]"):
    return f"""
<!-- BloodBridge Full UI — embedded inline for Colab -->
<!-- Full standalone version: open bloodbridge_ui.html -->
<div id="bb-root"></div>
<script>
  // Redirect to standalone file if available
  const iframe = document.createElement('iframe');
  iframe.src = 'bloodbridge_ui.html';
  iframe.style.cssText = 'width:100%;height:800px;border:none;';
  document.getElementById('bb-root').appendChild(iframe);
</script>
<noscript>Please open bloodbridge_ui.html directly in your browser.</noscript>
"""

print("✅ BloodBridge Extension Module Loaded.")
print("📋 New functions available:")
print("   recommend_donors_crosstype(patient)")
print("   simulate_hospital_ehr(patient_id)")
print("   get_inventory_status(request_id)")
print("   post_gratitude(request_id, patient_id, message)")
print("   get_gratitude_wall()")
print("   register_caregiver(patient_id, name, phone)")
print("   send_caregiver_alert(patient_id, stage)")
print("   check_donor_cooldown(donor_id)")
print("   mark_donation_complete_with_cooldown(donor_id, request_id)")
print("   plot_donor_health_trends(donor_id)")
print("   pre_donation_stress_gate(donor_id, free_text)")
print("   find_nearby_camps(lat, lon, radius_km)")
print("   register_blood_camp(name, lat, lon, date, organizer, contact)")
print("   cross_region_pool(region, blood_group, units)")
print("   train_donor_risk_net()")
print("   predict_donor_risk_net(bp, pulse, hb, dizziness)")
print("   donor_impact_dashboard(donor_id)")
print("   render_donor_map(request_id, patient)")
print("   launch_frontend_ui()")
