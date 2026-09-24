from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

ROLES = [
    "Software Engineer", "Data Analyst", "Customer Support Officer", "Marketing Assistant",
    "Warehouse Coordinator", "Graduate Developer", "Finance Assistant", "Research Intern",
    "Project Coordinator", "Cloud Support Engineer", "Business Analyst", "Administration Officer",
]
COMPANIES = [
    "Northstar Digital", "Harbour Analytics", "Rivergum Systems", "BluePeak Labs",
    "Southern Cross Services", "BrightPath Consulting", "Atlas Operations", "Cedar Technologies",
]
CITIES = ["Adelaide", "Melbourne", "Sydney", "Brisbane", "Perth", "Canberra"]

LEGIT_TEMPLATES = [
    "{company} is hiring a {role} in {city}. Please apply through our official careers page. Shortlisted candidates will complete an interview and reference checks. Salary is based on experience and the role includes standard employment benefits.",
    "We are seeking a {role} to join our {city} team. Responsibilities include collaborating with colleagues, documenting work and meeting project deadlines. Applications are reviewed by our recruitment team and selected applicants will be invited to a formal interview.",
    "Graduate opportunity: {role} at {company}. Submit your CV and cover letter through the company application portal. The recruitment process includes screening, a technical or behavioural interview and identity checks only after a conditional offer.",
    "{company} has an opening for a {role}. This is a full-time position based in {city}. Candidates should demonstrate relevant skills and experience. No payment is required at any stage of recruitment.",
]

SCAM_TEMPLATES = [
    "Dear candidate, you have been selected for a remote {role}. No interview required. Earn ${pay} per week working only 2 hours a day. Contact the recruiter on WhatsApp and deposit ${deposit} in USDT to activate your account.",
    "URGENT HIRING for {role}. Immediate start, guaranteed income ${pay} weekly. Message us on Telegram. A refundable registration fee of ${deposit} is required before onboarding.",
    "Congratulations applicant. You are hired immediately as a {role} for {company}. Send your passport and bank account details, then transfer ${deposit} to secure your equipment package.",
    "Work from home opportunity: {role}. Easy money, no experience needed, limited positions. Contact us on Signal and top up your crypto wallet with ${deposit} to begin tasks.",
    "Dear applicant, {company} is offering a {role} position. Respond within 2 hours. There is no formal interview. Send your TFN and driver's licence and pay a processing fee of ${deposit} by bank transfer.",
]


def build_rows(n: int, seed: int = 42):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        fraudulent = i % 2 == 1
        role = rng.choice(ROLES)
        company = rng.choice(COMPANIES)
        city = rng.choice(CITIES)
        if fraudulent:
            text = rng.choice(SCAM_TEMPLATES).format(
                role=role,
                company=company,
                city=city,
                pay=rng.choice([900, 1200, 1800, 2500]),
                deposit=rng.choice([50, 100, 150, 250, 500]),
            )
            # Add benign language sometimes so the examples are not perfectly separable by one phrase.
            if rng.random() < 0.25:
                text += " We provide training and a friendly team environment."
        else:
            text = rng.choice(LEGIT_TEMPLATES).format(role=role, company=company, city=city)
            if rng.random() < 0.25:
                text += " Flexible or remote work may be available depending on the team."
        rows.append({"text": text, "fraudulent": int(fraudulent), "source": "synthetic_demo"})
    rng.shuffle(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate transparent synthetic smoke-test data for JobShield AU.")
    parser.add_argument("--rows", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/demo_training.csv")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows(args.rows, args.seed)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "fraudulent", "source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
