# 🧠 FWC AI-HRMS

**An AI-powered Human Resource Management System that transforms how companies manage their workforce — from recruitment to retention.**

Built for the **FWC IT Services AI/ML Fullstack Hackathon** as a zero-dependency, production-ready HRMS with 5 integrated AI features powered by Claude.

---

## ✨ AI Features

| # | Feature | Description |
|---|---|---|
| 1 | **Smart Resume Screening** | AI analyses resumes against job requirements, scores 0–100, identifies skill gaps, and provides shortlist recommendations |
| 2 | **Interview Question Generator** | Creates tailored technical + behavioural interview questions based on candidate skills |
| 3 | **Performance Review Summariser** | Generates professional 3-sentence performance reviews with actionable next-step goals |
| 4 | **HR Chatbot** | Context-aware AI assistant that answers employee questions using real HR data (leave, attendance, salary, policies) |
| 5 | **Attrition Risk Predictor** | Predicts employee flight risk (Low/Medium/High) by analysing attendance, performance, tenure, and salary data |

All AI features gracefully degrade to rule-based fallback logic when the Claude API key is unavailable.

---

## 🖥 Core HRMS Modules

- **Role-based Authentication** — Admin, HR, Manager, Employee with tailored dashboards
- **Employee Management** — Full CRUD with department, designation, salary tracking
- **Attendance Tracking** — Individual + bulk CSV upload for HR/Admin
- **Leave Management** — Apply, approve, reject workflow with notifications
- **Payroll Calculation** — Automated salary computation with allowances and attendance-based deductions
- **Candidate Pipeline** — Track applicants with AI-powered resume scoring
- **Performance Reviews** — Manager-submitted reviews with AI summaries and attrition risk analysis
- **Notifications** — Real-time bell notifications for pending actions
- **Announcements** — Company-wide broadcast system (Admin only)

---

## 🏗 Architecture

```
Browser (Vanilla HTML/CSS/JS)
    │
    │ fetch() JSON API
    ▼
Node.js HTTP Server (zero dependencies)
    │               │
    ▼               ▼
JSON File DB    Claude API
(db.json)       (Anthropic)
```

> See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture diagram.  
> See [docs/API.md](docs/API.md) for complete API documentation.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Node.js — built-in `http`, `https`, `crypto`, `fs` modules |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES2020+) |
| Database | JSON flat file (no external DB required) |
| Authentication | Hand-rolled JWT (HMAC-SHA256 via `crypto`) |
| AI Engine | Claude API (claude-haiku-4-5) with rule-based fallback |
| Typography | Google Fonts — Syne + DM Sans |
| Voice Input | Web Speech API |
| Dependencies | **Zero** npm packages required |

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/fwc-ai-hrms.git
cd fwc-ai-hrms

# 2. (Optional) Set up environment variables
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY

# 3. Start the server
npm start

# 4. Open in browser
# http://localhost:3000
```

### Demo Credentials

| Email | Role | Password |
|---|---|---|
| `admin@fwc.demo` | Admin | `password123` |
| `hr@fwc.demo` | HR Recruiter | `password123` |
| `manager@fwc.demo` | Senior Manager | `password123` |
| `employee@fwc.demo` | Employee | `password123` |

---

## 📁 Project Structure

```
fwc/
├── backend/
│   ├── server.js          # All backend logic (HTTP server, API routes, AI features)
│   └── data/
│       └── db.json        # JSON flat-file database
├── frontend/
│   ├── index.html         # HTML shell
│   ├── styles.css         # Dark Command Center theme
│   └── app.js             # SPA frontend logic
├── docs/
│   ├── ARCHITECTURE.md    # System architecture diagram
│   ├── API.md             # Complete API documentation
│   └── ...                # Phase documentation
├── scripts/
│   └── smoke-test.js      # Automated API smoke tests
├── .env.example           # Environment variable template
├── package.json
└── README.md
```

---

## 🧪 Testing

```bash
# Run the smoke test suite
npm test
```

---

## 📝 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PORT` | No | `3000` | Server port |
| `TOKEN_SECRET` | No | `fwc-demo-...` | JWT signing secret |
| `ANTHROPIC_API_KEY` | No | — | Claude API key for AI features |

---

## 🎨 Design

The UI follows a **"Dark Command Center"** aesthetic:
- Deep navy background with subtle grid texture
- Glassmorphism cards with backdrop blur
- Electric cyan and hot coral accent colours
- Animated stat counters and typewriter AI responses
- Fully responsive — mobile hamburger sidebar at < 920px

---

## 👤 Author

Built for the FWC IT Services Pvt. Ltd. AI/ML with Fullstack Hackathon.

---

## 📄 Licence

MIT
