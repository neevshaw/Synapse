# Synapse

Synapse connects students who are learning tech skills with local businesses that need small tech projects done. Students work through short lessons (AI, app development, data analysis, web development, cloud, automation, and more), then apply to real projects that businesses post on the platform.

- **Website:** https://www.myquesttech.com/
- **Demo video:** https://youtu.be/3xPCN-udqB8

## Features

- **Student and business accounts.** Sign up, log in, and keep a profile (interests and location for students; industry, contact, and description for businesses).
- **Learning path.** A map of 10 units covering topics like chatbots, Flutter, Python data analysis, APIs, HTML/CSS/JS, e-commerce, and cloud services. Unit 1 has lessons and a quiz; the other units show a "coming soon" page.
- **Project board.** Businesses post projects with a deadline and description, and can mark them as fulfilled. Students browse projects and apply from the project page.
- **Application emails.** When a student applies, the app sends the business an email with the application through an AWS Lambda function.
- **AI student suggestions.** When posting a project, a business can ask for suggestions of which students fit it best, using Google Gemini.

## Tech stack

- Python / Flask, Flask-Login, Flask-SQLAlchemy
- MySQL (via PyMySQL), originally hosted on PythonAnywhere
- AWS Lambda + Gmail SMTP for outgoing email
- Google Gemini for project/student matching
- HTML/CSS templates (Jinja2)

## Repository layout

| Path | What it is |
|---|---|
| `flask_app.py` | The main Flask app: models, routes, auth, project board, and the `/match` endpoint |
| `lambda_function.py` | AWS Lambda handler that sends the application emails over SMTP |
| `match_projects.py` | See the note below |
| `templates/` | Page templates; `templates/unit1/` holds the Unit 1 lessons and quiz |
| `static/` | Stylesheet, logo, and favicon |

> **Note on `match_projects.py`:** `flask_app.py` imports a `match()` function from `match_projects.py`, but that file currently holds an older copy of the Flask app itself and doesn't define `match()`. To run the app, either add the Gemini matching function (`match(api_key, project_data, students) -> str`) to `match_projects.py` or remove the import and the `/match` route.

## Running locally

1. Install the dependencies:
   ```bash
   pip install flask flask-sqlalchemy flask-login pymysql python-dotenv requests google-genai
   ```
2. Create a `.env` file with the variables listed below. By default the app loads `~/mysite/.env` (the PythonAnywhere layout). Change `project_folder` at the top of `flask_app.py` if your `.env` file lives somewhere else.
3. Start the app:
   ```bash
   python flask_app.py
   ```
   The database tables are created automatically on first run.

### Environment variables

**Flask app (`flask_app.py`)**

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session secret |
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME` | MySQL connection details |
| `LAMBDA` | URL of the deployed email Lambda (function URL or API Gateway) |
| `GEMINI_API` | Google Gemini API key used by `/match` |

**Email Lambda (`lambda_function.py`)**

| Variable | Purpose |
|---|---|
| `username` | Sender email address (Gmail) |
| `password` | App password for that account |

Never commit `.env` files. They're listed in `.gitignore`.
