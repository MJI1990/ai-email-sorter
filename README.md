# AI Email Sorter

Overview
This project is an AI-powered email automation tool that reads emails, classifies them, and stores the results in a structured format.

Features
- Read unread emails from Gmail
- Classify emails into categories:
  - Important
  - Urgent
  - Complaint
  - Normal
- Extract:
  - Sender
  - Subject
  - Email content
- Save results into CSV file

 Technologies Used
- Python
- Gmail API
- OpenAI API
- Pandas

How It Works
1. Fetch unread emails using Gmail API
2. Process email content
3. Use AI to classify email type
4. Save results into CSV file

How to Run
1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt

Installation

```bash
git clone https://github.com/MJI1990/ai-email-sorter.git
cd ai-email-sorter
pip install -r requirements.txt
