import os
import subprocess

docs = {
    "product_spec_v3.md": "# Product Specification v3.2\n\nThe Hanu InnoTech IoT Sensor operates at 5V and has a temperature accuracy of +/- 0.1C. The calibration procedure involves exposing the sensor to 25C for 10 minutes.\n\n## Limits\n- Max Voltage: 5.5V\n- Max Temp: 85C\n",
    "employee_handbook.md": "# Employee Handbook 2026\n\nWelcome to Hannu InnoTech (Hanumayamma Innovations and Technologies Inc.). Our standard PTO is 20 days per year. Remote work is supported up to 3 days a week.\n\n## About the Company\nHannu InnoTech is our internal brand. Our parent company Hanumayamma Innovations and Technologies Inc. is a U.S. Delaware corporation founded in 2010, focused on agriculture analytics, dairy analytics, IoT sensors, and AI for farmers worldwide. Official website: https://www.hanuinnotech.com/\n\n## Code of Conduct\nBe respectful and innovative.",
    "board_meeting_june.md": "# Board Meeting Notes - June 2026\n\nThe board discussed the potential M&A with SensorCorp. We are considering an offer of $45M. This information is strictly restricted.\n"
}

def generate_samples():
    os.makedirs("sample_docs", exist_ok=True)
    for filename, content in docs.items():
        path = os.path.join("sample_docs", filename)
        with open(path, "w") as f:
            f.write(content)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scrape_script = os.path.join(script_dir, "scrape_hanuinnotech_website.py")
    if os.path.exists(scrape_script):
        subprocess.run(["python", scrape_script], cwd=script_dir, check=False)
    print("Sample documents generated.")

if __name__ == "__main__":
    generate_samples()
