# MATH 1710 Precalculus AI Tutoring System

**Dr. April Crenshaw • Chattanooga State Community College**

An intelligent tutoring system that provides personalized, adaptive scaffolding for precalculus students. Built with FastAPI, OpenAI GPT-4, and Firebase.

---

## 🎯 Features

### **Adaptive Learning Modes**
- **Quick Hints** - Minimal scaffolding with multiple choice questions for confident students
- **Walk Me Through It** - Step-by-step guided problem solving
- **Teach Me More** - Detailed explanations with conceptual depth

### **Intelligent Scaffolding**
- Real-time answer validation with support for equivalent forms (fractions, decimals, radicals)
- Progressive hint escalation when students struggle
- Automatic mode switching based on student performance
- Comprehension checks every 3 steps

### **Student Success Tracking**
- Session-based progress monitoring
- Calculator usage tracking
- Wrong answer attempt tracking
- Problem completion metrics
- Weekly usage reports with success indicators

### **Multi-language Support**
- English (primary)
- Spanish with auto-translation
- Custom language support

---

## 📁 Project Structure

```
math1710-tutor/
├── 📄 Production Files (root level)
│   ├── app.py                      # Main FastAPI application
│   ├── config.py                   # Course configuration
│   ├── prompts.py                  # Teaching prompts & AI instructions
│   ├── fast_validator.py           # Answer validation system
│   ├── firebase_service.py         # Cloud database integration
│   ├── backup_service.py           # Automatic session backups
│   ├── email_service.py            # Email notification service
│   ├── index.html                  # Student interface
│   ├── tutor_interface.html        # Instructor interface
│   └── usage_report_optimized.html # Usage analytics dashboard
│
├── 📚 docs/                        # Documentation
│   ├── deployment/                 # Deployment guides
│   ├── architecture/               # System architecture docs
│   ├── analysis/                   # Performance & optimization analysis
│   └── changes/                    # Change logs & summaries
│
├── 🗄️ archive/                    # Archived/variant files
├── 🔧 utils/                       # Utility scripts
└── 🌐 presentation/                # Presentation materials
```

---

## 🚀 Quick Start

### **Prerequisites**
```bash
pip install fastapi uvicorn openai python-dotenv firebase-admin pytz
```

### **Environment Variables**
Create a `.env` file:
```bash
OPENAI_API_KEY=your-openai-api-key
FIREBASE_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'
```

### **Run the Application**
```bash
# Development mode (with auto-reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000
```

### **Access Interfaces**
- **Student Interface:** http://localhost:8000/
- **Tutor Interface:** http://localhost:8000/tutor
- **Usage Report:** http://localhost:8000/usage-report

---

## 📖 Key Documentation

### For Students
- **[Student Guide](STUDENT_GUIDE.md)** - How to use the tutoring system

### For Instructors/Developers
- **[Deployment Guide](docs/deployment/FINAL_DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Email Setup Guide](docs/deployment/EMAIL_SETUP_GUIDE.md)** - Configure email notifications
- **[Architecture Overview](docs/architecture/README_PROMPTS.md)** - System architecture and design
- **[Backend Implementation](docs/deployment/BACKEND_IMPLEMENTATION_GUIDE.md)** - Backend setup details

### For Developers
- **[Prompts Documentation](docs/architecture/README_PROMPTS.md)** - Teaching prompt system
- **[Config Changes](docs/architecture/README_CONFIG_CHANGES.md)** - Configuration options
- **[Answer Validation](docs/architecture/README_ANSWER_VALIDATION_EFFICIENCY.md)** - Validation system details
- **[Performance Optimization](docs/analysis/OPTIMIZATION_SUMMARY.md)** - Performance improvements

---

## 🎓 Teaching Philosophy

This system implements research-based teaching strategies:

✅ **Socratic Method** - Guide students to discover solutions through questioning
✅ **Zone of Proximal Development** - Adaptive scaffolding based on student needs
✅ **Growth Mindset** - Normalize struggle, celebrate effort
✅ **Metacognitive Support** - Help students understand their own thinking
✅ **Mastery Learning** - Focus on understanding, not just answers

---

## 🔧 Core Components

### **1. Adaptive Prompting System** (`prompts.py`)
- 72KB of carefully crafted AI instructions
- Mode-specific teaching strategies
- Critical rules enforcement (multiple choice format, answer acceptance, scaffolding)
- Comprehension checking and reteaching protocols

### **2. Answer Validation** (`fast_validator.py`)
- Fast multiple choice option extraction
- Equivalent answer form recognition (1/2 = 0.5 = .5)
- Programmatic validation with AI fallback
- Performance optimized for real-time feedback

### **3. Session Management** (`app.py`)
- In-memory session storage with automatic cleanup
- Progress tracking (wrong attempts, calculator usage, completion)
- Automatic Firebase backup every 12 hours
- RESTful API endpoints for all interactions

### **4. Firebase Integration** (`firebase_service.py`)
- Cloud-based session persistence
- Student progress tracking
- Usage analytics
- Automatic error handling and retry logic

### **5. Email Notifications** (`email_service.py`)
- Weekly usage digest (Fridays)
- Problem report notifications
- SMTP integration with Gmail/institutional email

---

## 📊 Usage Reports

The system provides comprehensive analytics:

- **Session Metrics**: Total sessions, average duration, completion rates
- **Problem Solving**: Problems attempted vs. completed, success rates
- **Student Engagement**: Calculator usage, wrong attempt patterns
- **Mode Preferences**: Which learning modes students choose
- **Time Analysis**: Peak usage times, session duration trends

Access the live dashboard at `/usage-report` (instructor access only).

---

## 🛠️ Configuration

### **Course Settings** (`config.py`)
Configure course information, problem sets, teaching philosophy, and scaffolding modes.

Key configuration sections:
- `COURSE` - Course metadata (code, name, instructor)
- `TOPIC_MODULES` - Problem sets by unit
- `SCAFFOLDING_MODES` - Learning mode definitions
- `EMAIL_SETTINGS` - Email notification configuration
- `AI_SETTINGS` - Model parameters (temperature, max tokens, timeout)

### **Teaching Prompts** (`prompts.py`)
Customize AI teaching behavior:
- Mode-specific instructions (Quick Hints, Step-by-Step, Detailed)
- Scaffolding strategies
- Error handling protocols
- Comprehension check frequency

---

## 🔒 Security & Privacy

- No student PII stored (sessions use anonymous IDs)
- Firebase security rules enforce access control
- Email notifications respect FERPA guidelines
- API rate limiting prevents abuse
- Environment variables for sensitive credentials

---

## 📈 Recent Improvements

### November 2025 Updates
✅ **Quick Hints Mode**: Now uses multiple choice format exclusively
✅ **Answer Validation**: Accepts equivalent forms (fractions ↔ decimals)
✅ **Scaffolding**: D is always "I'm not sure", proper fallback behavior
✅ **Session Tracking**: Enhanced metrics (calculator usage, wrong attempts, completion)
✅ **Clean Results**: No intermediate arithmetic shown in Quick Hints mode

See [docs/changes/](docs/changes/) for detailed change logs.

---

## 🤝 Contributing

This is an educational research project. For questions or collaboration:

**Dr. April Crenshaw**
Chattanooga State Community College
april.crenshaw@chattanoogastate.edu

---

## 📝 License

Educational use only. Contact Dr. Crenshaw for licensing inquiries.

---

## 🙏 Acknowledgments

Built with Claude AI assistance for the STEM Conference 2025.

**Technology Stack:**
- FastAPI (Python web framework)
- OpenAI GPT-4 (AI reasoning)
- Firebase (cloud database)
- JavaScript/HTML/CSS (frontend)

---

**Last Updated:** November 2025
