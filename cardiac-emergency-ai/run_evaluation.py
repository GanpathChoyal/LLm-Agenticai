"""
Cardiac Emergency AI — Full Evaluation Metrics Script
Computes ALL 8 metrics from the evaluation_metrics.md document
using actual data from the Django database.
"""
import os
import sys
import json
import io
import django

# Fix Windows terminal encoding for emoji/unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardiac_project.settings")
django.setup()

from django.db.models import Avg, Max, Min, Count, StdDev, Q
from emergency.models import DiagnosticReport, Patient, DiagnosticInput

# ─────────────────────────────────────────
# Helper
# ─────────────────────────────────────────
def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def safe_pct(num, den):
    return (num / den * 100) if den > 0 else 0.0

# ─────────────────────────────────────────
reports = DiagnosticReport.objects.all()
total = reports.count()

if total == 0:
    print("No reports in database. Run the pipeline first.")
    sys.exit(1)

print(f"\n📊 CARDIAC EMERGENCY AI — EVALUATION REPORT")
print(f"   Total reports in database: {total}")
print(f"   Total patients: {Patient.objects.count()}")

# ═══════════════════════════════════════════
# METRIC 1: Risk Classification Distribution
# (Full accuracy needs ground truth — we show distribution + what we CAN measure)
# ═══════════════════════════════════════════
section("METRIC 1: Risk Level Distribution")

risk_counts = {}
for choice in ["LOW", "MODERATE", "HIGH", "CRITICAL", "INCONCLUSIVE"]:
    count = reports.filter(risk_level=choice).count()
    risk_counts[choice] = count

print(f"\n  {'Risk Level':<16} {'Count':>6} {'Percentage':>12}")
print(f"  {'-'*36}")
for level, count in risk_counts.items():
    pct = safe_pct(count, total)
    bar = "█" * int(pct / 2)
    print(f"  {level:<16} {count:>6} {pct:>10.1f}%  {bar}")

# Check for bias: if >80% is one class, flag it
max_class = max(risk_counts, key=risk_counts.get)
max_pct = safe_pct(risk_counts[max_class], total)
if max_pct > 80:
    print(f"\n  ⚠️  WARNING: {max_pct:.0f}% of reports are '{max_class}' — possible class imbalance")
elif max_pct > 60:
    print(f"\n  ⚡ NOTE: {max_pct:.0f}% of reports are '{max_class}' — skewed distribution")
else:
    print(f"\n  ✅ Distribution looks balanced across risk levels")

# ═══════════════════════════════════════════
# METRIC 2: Agent Concordance Rate
# ═══════════════════════════════════════════
section("METRIC 2: Agent Concordance Rate")

agreed = reports.filter(agent_agreement=True).count()
discordant = reports.filter(agent_agreement=False).count()
concordance_rate = safe_pct(agreed, total)

print(f"\n  Agents Agreed:     {agreed:>4} reports")
print(f"  Agents Discordant: {discordant:>4} reports")
print(f"  Concordance Rate:  {concordance_rate:.1f}%")

if concordance_rate > 85:
    print(f"  ✅ Strong concordance — agents usually agree")
elif concordance_rate > 60:
    print(f"  ⚡ Moderate concordance — review discordant cases")
else:
    print(f"  ⚠️  Low concordance — agents frequently disagree, needs tuning")

# Show which agents are most often discordant
discordant_reports = reports.exclude(discordant_agents=[]).exclude(discordant_agents__isnull=True)
agent_discord_count = {}
for r in discordant_reports:
    agents = r.discordant_agents if isinstance(r.discordant_agents, list) else []
    for a in agents:
        agent_discord_count[a] = agent_discord_count.get(a, 0) + 1

if agent_discord_count:
    print(f"\n  Most Frequently Discordant Agents:")
    for agent, count in sorted(agent_discord_count.items(), key=lambda x: -x[1]):
        print(f"    - {agent}: {count} times")

# ═══════════════════════════════════════════
# METRIC 3: Critic Agent Effectiveness
# ═══════════════════════════════════════════
section("METRIC 3: Critic Agent Effectiveness")

# Check if critic_output is stored anywhere
# The critic output isn't a direct DB field, but we can infer from loop_count
# If loop_count > 1, the critic likely challenged at least once
multi_loop = reports.filter(loop_count__gte=2).count()
single_loop = reports.filter(loop_count__lte=1).count()

# Try to check if any report has critic data in its JSON fields
critic_challenged = 0
critic_approved = 0
critic_data_available = False

for r in reports:
    # Check if ecg/biomarker/imaging findings contain critic info
    # The critic_output isn't stored in DB directly, so we infer
    pass

print(f"\n  Reports resolved in 1 loop (critic approved):  {single_loop}")
print(f"  Reports needing 2+ loops (critic challenged):  {multi_loop}")
estimated_challenge_rate = safe_pct(multi_loop, total)
print(f"  Estimated Challenge Rate: {estimated_challenge_rate:.1f}%")

if estimated_challenge_rate == 0:
    print(f"  ⚠️  Critic never challenged — may be rubber-stamping")
elif estimated_challenge_rate <= 20:
    print(f"  ✅ Healthy challenge rate (5-20% is ideal)")
elif estimated_challenge_rate <= 40:
    print(f"  ⚡ High challenge rate — critic may be too aggressive")
else:
    print(f"  ⚠️  Very high challenge rate — review critic prompt")

print(f"\n  💡 TIP: To get exact critic verdicts, store critic_output in DiagnosticReport")

# ═══════════════════════════════════════════
# METRIC 4: Confidence Calibration
# ═══════════════════════════════════════════
section("METRIC 4: Confidence Score Analysis")

conf_stats = reports.aggregate(
    avg=Avg("confidence_score"),
    max_val=Max("confidence_score"),
    min_val=Min("confidence_score"),
    std=StdDev("confidence_score")
)

print(f"\n  Average Confidence:  {conf_stats['avg']:.1f}%")
print(f"  Min Confidence:      {conf_stats['min_val']:.1f}%")
print(f"  Max Confidence:      {conf_stats['max_val']:.1f}%")
print(f"  Std Deviation:       {conf_stats['std']:.1f}%")

# Confidence distribution by bucket
buckets = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
for r in reports:
    score = r.confidence_score or 0
    if score < 25:   buckets["0-25"] += 1
    elif score < 50: buckets["25-50"] += 1
    elif score < 75: buckets["50-75"] += 1
    else:            buckets["75-100"] += 1

print(f"\n  {'Bucket':<12} {'Count':>6} {'Percentage':>12}")
print(f"  {'-'*32}")
for bucket, count in buckets.items():
    pct = safe_pct(count, total)
    bar = "█" * int(pct / 2)
    print(f"  {bucket+'%':<12} {count:>6} {pct:>10.1f}%  {bar}")

# Confidence by risk level
print(f"\n  Average Confidence by Risk Level:")
for level in ["LOW", "MODERATE", "HIGH", "CRITICAL", "INCONCLUSIVE"]:
    level_reports = reports.filter(risk_level=level)
    if level_reports.exists():
        avg_conf = level_reports.aggregate(avg=Avg("confidence_score"))["avg"]
        count = level_reports.count()
        print(f"    {level:<16} → {avg_conf:.1f}% confidence  (n={count})")

# Flag overconfidence
high_conf_count = reports.filter(confidence_score__gte=90).count()
overconf_pct = safe_pct(high_conf_count, total)
if overconf_pct > 70:
    print(f"\n  ⚠️  {overconf_pct:.0f}% of reports have >90% confidence — possible overconfidence")
else:
    print(f"\n  ✅ Confidence distribution looks reasonable")

# ═══════════════════════════════════════════
# METRIC 5: Pipeline Latency
# ═══════════════════════════════════════════
section("METRIC 5: Pipeline Latency (Processing Time)")

time_reports = reports.exclude(processing_time_seconds__isnull=True)
time_count = time_reports.count()

if time_count > 0:
    time_stats = time_reports.aggregate(
        avg=Avg("processing_time_seconds"),
        max_val=Max("processing_time_seconds"),
        min_val=Min("processing_time_seconds"),
        std=StdDev("processing_time_seconds")
    )
    
    avg_time = time_stats['avg']
    max_time = time_stats['max_val']
    min_time = time_stats['min_val']
    
    print(f"\n  Reports with timing data: {time_count}")
    print(f"  Average Processing Time: {avg_time:.1f}s")
    print(f"  Fastest:                 {min_time:.1f}s")
    print(f"  Slowest:                 {max_time:.1f}s")
    if time_stats['std']:
        print(f"  Std Deviation:           {time_stats['std']:.1f}s")
    
    # Time buckets
    under_30 = time_reports.filter(processing_time_seconds__lt=30).count()
    under_60 = time_reports.filter(processing_time_seconds__gte=30, processing_time_seconds__lt=60).count()
    over_60 = time_reports.filter(processing_time_seconds__gte=60).count()
    
    print(f"\n  {'Time Range':<16} {'Count':>6} {'Status':>12}")
    print(f"  {'-'*36}")
    print(f"  {'< 30 sec':<16} {under_30:>6} {'🟢 Excellent':>12}")
    print(f"  {'30-60 sec':<16} {under_60:>6} {'🟡 OK':>12}")
    print(f"  {'> 60 sec':<16} {over_60:>6} {'🔴 Too Slow':>12}")
    
    if avg_time < 30:
        print(f"\n  ✅ Average {avg_time:.0f}s — well within the 60s ER target")
    elif avg_time < 60:
        print(f"\n  ⚡ Average {avg_time:.0f}s — within target but could improve")
    else:
        print(f"\n  ⚠️  Average {avg_time:.0f}s — EXCEEDS the 60s ER target!")
else:
    print(f"\n  ⚠️  No timing data available")

# ═══════════════════════════════════════════
# METRIC 6: Loop Efficiency
# ═══════════════════════════════════════════
section("METRIC 6: Loop Efficiency (Reasoning Iterations)")

loop_stats = reports.aggregate(
    avg=Avg("loop_count"),
    max_val=Max("loop_count"),
    min_val=Min("loop_count")
)

print(f"\n  Average Loops: {loop_stats['avg']:.2f}")
print(f"  Min Loops:     {loop_stats['min_val']}")
print(f"  Max Loops:     {loop_stats['max_val']}")

# Loop distribution
for i in range(0, 4):
    count = reports.filter(loop_count=i).count()
    pct = safe_pct(count, total)
    bar = "█" * int(pct / 2)
    label = f"{i} loop{'s' if i != 1 else ''}"
    print(f"  {label:<12} {count:>4} ({pct:.0f}%)  {bar}")

max_loop_cases = reports.filter(loop_count__gte=2).count()
max_loop_pct = safe_pct(max_loop_cases, total)
if max_loop_pct > 30:
    print(f"\n  ⚠️  {max_loop_pct:.0f}% need 2+ loops — Reasoning Agent may need prompt tuning")
elif max_loop_pct > 10:
    print(f"\n  ⚡ {max_loop_pct:.0f}% need reanalysis — acceptable")
else:
    print(f"\n  ✅ Most cases resolve in 1 pass — efficient pipeline")

# ═══════════════════════════════════════════
# METRIC 7: Extraction Accuracy (what we can measure)
# ═══════════════════════════════════════════
section("METRIC 7: Extraction Coverage (Data Completeness)")

inputs = DiagnosticInput.objects.all()
input_count = inputs.count()

if input_count > 0:
    fields = ["heart_rate", "systolic_bp", "troponin", "bnp", "ldl", "hba1c", "creatinine", "ckmb"]
    
    print(f"\n  Total diagnostic inputs: {input_count}")
    print(f"\n  {'Field':<16} {'Filled':>8} {'Empty':>8} {'Fill Rate':>12}")
    print(f"  {'-'*46}")
    
    total_filled = 0
    total_fields = 0
    
    for field in fields:
        filled = inputs.exclude(**{f"{field}__isnull": True}).count()
        empty = input_count - filled
        rate = safe_pct(filled, input_count)
        total_filled += filled
        total_fields += input_count
        status = "✅" if rate > 70 else "⚡" if rate > 40 else "⚠️"
        print(f"  {field:<16} {filled:>8} {empty:>8} {rate:>10.1f}%  {status}")
    
    overall_fill = safe_pct(total_filled, total_fields)
    print(f"\n  Overall Field Fill Rate: {overall_fill:.1f}%")
    
    # File uploads
    has_report = inputs.exclude(report_file="").exclude(report_file__isnull=True).count()
    has_ecg = inputs.exclude(ecg_file="").exclude(ecg_file__isnull=True).count()
    has_echo = inputs.exclude(echo_file="").exclude(echo_file__isnull=True).count()
    
    print(f"\n  File Uploads:")
    print(f"    Report files: {has_report}/{input_count} ({safe_pct(has_report, input_count):.0f}%)")
    print(f"    ECG files:    {has_ecg}/{input_count} ({safe_pct(has_ecg, input_count):.0f}%)")
    print(f"    Echo files:   {has_echo}/{input_count} ({safe_pct(has_echo, input_count):.0f}%)")
    
    print(f"\n  💡 For exact extraction accuracy, compare extracted values vs known values in test reports")
else:
    print(f"\n  ⚠️  No diagnostic inputs found")

# ═══════════════════════════════════════════
# METRIC 8: Doctor Feedback Rate
# ═══════════════════════════════════════════
section("METRIC 8: Doctor Confirmation Rate")

confirmed = reports.filter(doctor_confirmed=True).count()
overridden = reports.filter(doctor_override=True).count()
pending = reports.filter(doctor_confirmed=False, doctor_override=False).count()

print(f"\n  Doctor Confirmed: {confirmed:>4} ({safe_pct(confirmed, total):.1f}%)")
print(f"  Doctor Overridden:{overridden:>4} ({safe_pct(overridden, total):.1f}%)")
print(f"  Pending Review:   {pending:>4} ({safe_pct(pending, total):.1f}%)")

if overridden > 0:
    override_rate = safe_pct(overridden, confirmed + overridden)
    print(f"\n  Override Rate (of reviewed): {override_rate:.1f}%")
    if override_rate > 20:
        print(f"  ⚠️  High override rate — system may be inaccurate")
    else:
        print(f"  ✅ Low override rate — doctors mostly agree with AI")

# ═══════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════
section("OVERALL SYSTEM HEALTH SUMMARY")

print(f"""
  📊 Reports Analyzed:         {total}
  🤝 Agent Concordance:        {concordance_rate:.1f}%
  🎯 Avg Confidence:           {conf_stats['avg']:.1f}%
  ⏱️  Avg Processing Time:     {time_stats['avg']:.1f}s (target: <60s)
  🔄 Avg Loops:                {loop_stats['avg']:.2f}
  🔍 Critic Challenge Rate:    {estimated_challenge_rate:.1f}%
  👨‍⚕️ Doctor Confirmation Rate: {safe_pct(confirmed, total):.1f}%
""" if time_count > 0 else f"""
  📊 Reports Analyzed:         {total}
  🤝 Agent Concordance:        {concordance_rate:.1f}%
  🎯 Avg Confidence:           {conf_stats['avg']:.1f}%
  🔄 Avg Loops:                {loop_stats['avg']:.2f}
  🔍 Critic Challenge Rate:    {estimated_challenge_rate:.1f}%
  👨‍⚕️ Doctor Confirmation Rate: {safe_pct(confirmed, total):.1f}%
""")

print("  ⚠️  NOTE: Clinical accuracy (Metric 1 - Precision/Recall/F1) requires")
print("  ground truth labels. Use PTB-XL dataset or doctor review to compute.")
print(f"\n{'='*60}")
