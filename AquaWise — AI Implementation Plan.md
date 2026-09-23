AquaWise — AI Implementation Plan


1. Purpose


This document is the implementation roadmap for building the AquaWise — Water Conservation Recommendation System as a complete, functional web application.


The AI development agent must use this document together with the following project documents:


1. AquaWise — Project Requirements Document
2. AquaWise — Technical Requirements Document
3. AquaWise — App Flow Document
4. AquaWise — UI/UX Design Brief
5. AquaWise — Backend Schema Document


These documents together define the application's requirements, architecture, user experience, database structure, and implementation direction.


If two requirements appear to conflict, prioritize them in this order:


Project Requirements
        ↓
Technical Requirements
        ↓
Backend Schema
        ↓
App Flow
        ↓
UI/UX Design Brief
        ↓
Implementation Plan


The implementation must produce a working application, not just static mockup pages.


---


2. Primary Objective


Build AquaWise as a full-stack web application that allows users to:


Register/Login
      ↓
Select User Type
      ↓
Enter Water Usage Information
      ↓
Calculate Estimated Consumption
      ↓
Understand Consumption Breakdown
      ↓
Receive Personalized Recommendations
      ↓
Track Water Saver Score
      ↓
View Dashboard
      ↓
Compare Historical Usage
      ↓
Interact with AI Assistant


The application must be functional from end to end.


---


3. Technology Stack


Use the following stack unless there is a strong technical reason to change something:


Frontend


- HTML5
- CSS3
- JavaScript ES6+
- Chart.js


Backend


- Python 3
- Flask
- Flask-compatible REST API architecture


Database


- SQLite
- SQLAlchemy ORM


Authentication


- Flask-Login or an equivalent secure session-based implementation
- Werkzeug password hashing


AI


Use an external LLM API through the backend.


The AI provider must be configurable through environment variables.


Development


- Git
- GitHub
- VS Code


---


4. Implementation Principles


Follow these principles throughout development.


4.1 Build a real application


Do not create a collection of disconnected HTML mockups.


All major pages must communicate with the backend where required.


---


4.2 Separate responsibilities


Use a clear architecture:


Frontend
    ↓
API Routes
    ↓
Business Logic / Services
    ↓
Database


Do not put complex business logic directly inside HTML or JavaScript.


---


4.3 Deterministic calculations


Water consumption calculations must be performed by deterministic backend code.


Do not ask an AI model to calculate the user's water consumption.


The AI may explain or personalize the results, but it must not be the source of truth for numerical calculations.


---


4.4 AI is an enhancement


The application must remain functional even if the AI service is unavailable.


The following must work without AI:


- Authentication
- Assessment
- Consumption calculation
- Results
- Dashboard
- History
- Rule-based recommendations


---


4.5 Use modular code


Avoid creating one extremely large file.


Separate:


- Routes
- Models
- Services
- Utilities
- Frontend scripts
- Stylesheets


---


4.6 Avoid unnecessary complexity


This is an academic project that should demonstrate a complete working system.


Prefer:


Simple + reliable + understandable


over:


Over-engineered + difficult to maintain


---


5. Project Structure


Create the following structure:


AquaWise/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env
├── .env.example
├── .gitignore
│
├── frontend/
│   ├── templates/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── user_type.html
│   │   ├── assessment.html
│   │   ├── results.html
│   │   ├── dashboard.html
│   │   ├── history.html
│   │   ├── profile.html
│   │   └── assistant.html
│   │
│   └── static/
│       ├── css/
│       │   └── styles.css
│       │
│       ├── js/
│       │   ├── main.js
│       │   ├── auth.js
│       │   ├── assessment.js
│       │   ├── dashboard.js
│       │   ├── history.js
│       │   └── assistant.js
│       │
│       └── assets/
│
├── backend/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── assessment.py
│   │   ├── dashboard.py
│   │   ├── assistant.py
│   │   └── profile.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── assessment.py
│   │   ├── usage.py
│   │   ├── recommendation.py
│   │   ├── ai.py
│   │   └── gamification.py
│   │
│   ├── services/
│   │   ├── calculation_service.py
│   │   ├── recommendation_service.py
│   │   ├── scoring_service.py
│   │   └── ai_service.py
│   │
│   └── utils/
│       ├── validators.py
│       └── constants.py
│
├── database/
│   └── aquawise.db
│
└── tests/
    ├── test_auth.py
    ├── test_calculations.py
    ├── test_recommendations.py
    └── test_api.py


Adjust the exact structure if necessary, but maintain the same architectural separation.


---


6. Implementation Sequence


Implement the application in the following sequence.


Do not attempt to implement everything simultaneously.


STEP 1
Project setup
      ↓
STEP 2
Flask application
      ↓
STEP 3
Database models
      ↓
STEP 4
Authentication
      ↓
STEP 5
Frontend foundation
      ↓
STEP 6
Assessment system
      ↓
STEP 7
Calculation engine
      ↓
STEP 8
Recommendation engine
      ↓
STEP 9
Results page
      ↓
STEP 10
Dashboard
      ↓
STEP 11
History
      ↓
STEP 12
AI assistant
      ↓
STEP 13
Gamification
      ↓
STEP 14
Integration
      ↓
STEP 15
Testing and refinement


---


7. Step 1 — Project Setup


Create the Flask project and required directories.


Create:


app.py
config.py
requirements.txt
.env.example
.gitignore
README.md


Set up a Python virtual environment.


Add required dependencies to "requirements.txt".


At minimum, include the packages required for:


- Flask
- SQLAlchemy
- Authentication
- Password hashing
- Environment variables
- AI API communication
- Testing


The exact package versions should be compatible with one another.


---


8. Step 2 — Flask Application


Create the main Flask application.


The application must:


- Initialize Flask.
- Load configuration.
- Initialize the database.
- Register route blueprints.
- Serve frontend pages.
- Handle errors.
- Start successfully with a simple command.


The application should be organized so that routes are not all written inside "app.py".


---


9. Step 3 — Database


Implement the database according to the Backend Schema Document.


Required entities:


User
Assessment
HouseholdUsageDetails
FarmerUsageDetails
ConsumptionBreakdown
Recommendation
AIConversation
AIMessage
Achievement
UserAchievement
Streak


Implement appropriate:


- Primary keys
- Foreign keys
- Relationships
- Data types
- Constraints
- Timestamps


Make sure user-owned information is associated with the correct user.


---


10. Step 4 — Authentication


Implement:


Registration


Name
Email
Password
User Type


Login


Email
Password


Logout


Current-user session


The backend must securely hash passwords.


Never store plaintext passwords.


Authenticated API routes must verify that the current user owns the data being accessed.


A user must never be able to retrieve another user's assessments by changing an ID in the request.


---


11. Step 5 — Frontend Foundation


Create the main visual design system according to the UI/UX Design Brief.


Visual direction


Use:


- Light mode
- White/light neutral backgrounds
- Blue accents
- Green accents
- Professional typography
- Clean spacing
- Subtle shadows
- Consistent components


The design should feel like a real environmental technology product.


It should not look like a generic college project or an excessively colorful dashboard.


---


12. Step 6 — Authentication Pages


Implement:


/login
/register


Login page


Include:


- Email
- Password
- Login button
- Link to registration
- AquaWise branding
- Water/nature themed visual element


Register page


Include:


- Name
- Email
- Password
- User type


Provide clear validation and error messages.


After successful authentication, redirect the user appropriately.


---


13. Step 7 — User Type Selection


Support two primary user types:


Household
Farmer / Agricultural


Display these as clear selection cards.


The selected type determines which assessment form is shown.


---


14. Step 8 — Assessment System


Implement separate assessment flows.


Household Assessment


Collect:


Household size
Showers per day
Average shower duration
Toilet usage
Laundry frequency
Kitchen usage
Vehicle washing frequency
Gardening frequency
Gardening duration
Other water usage


Validate all inputs.


---


Farmer Assessment


Collect:


Farm area
Farm area unit
Crop type
Irrigation method
Irrigation frequency
Irrigation duration
Water source
Rainfall information
Rainwater harvesting
Estimated irrigation information


Use appropriate controls such as:


- Number inputs
- Dropdowns
- Radio buttons
- Checkboxes
- Text fields where appropriate


Do not overwhelm the user with unnecessary fields.


---


15. Step 9 — Calculation Engine


Create:


backend/services/calculation_service.py


The calculation service must:


1. Receive validated assessment data.
2. Calculate category-level consumption.
3. Calculate total daily consumption.
4. Calculate weekly consumption.
5. Calculate monthly consumption.
6. Return structured results.


Example:


{
    "daily_consumption": 290,
    "weekly_consumption": 2030,
    "monthly_consumption": 8700,
    "breakdown": {
        "shower": 120,
        "kitchen": 60,
        "laundry": 40,
        "gardening": 50,
        "other": 20
    }
}


The numerical assumptions must be centralized and easy to modify.


Clearly distinguish between:


- User-provided values
- Estimated values
- Application assumptions


Do not present estimates as exact measurements.


---


16. Step 10 — Recommendation Engine


Create:


backend/services/recommendation_service.py


Initially implement a deterministic rule-based system.


Examples:


High shower consumption
        ↓
Recommend shorter showers


High gardening consumption
        ↓
Recommend efficient watering practices


Frequent vehicle washing
        ↓
Recommend reducing unnecessary washing


Each recommendation should contain:


Category
Title
Description
Priority
Source


The system should be able to generate multiple recommendations.


Recommendations should be based on the user's actual assessment data.


Do not generate completely generic recommendations when user-specific information is available.


---


17. Step 11 — Water Saver Score


Create:


backend/services/scoring_service.py


Generate a Water Saver Score using documented application rules.


The score should be:


- Deterministic
- Reproducible
- Explainable


If the user completes another assessment, the system may compare it with previous data to identify improvement.


The score should be presented as an application indicator, not a scientific certification.


---


18. Step 12 — Results Page


Create a results page that displays:


Summary


Daily consumption
Weekly consumption
Monthly consumption
Water Saver Score


Breakdown


Display major water-use categories.


Use Chart.js where useful.


Possible charts:


Donut chart
Category consumption


Bar chart
Water usage by category


Recommendations


Show the most relevant recommendations prominently.


Include an option to continue to the dashboard.


---


19. Step 13 — Dashboard


The dashboard should be the user's main authenticated home page.


Display:


Current water consumption
Water Saver Score
Current streak
Top recommendation
Recent assessment


Include useful charts such as:


- Consumption trend
- Category breakdown
- Weekly/monthly comparison


The dashboard should prioritize important information rather than displaying every available database field.


Provide access to:


New Assessment
History
AI Assistant
Profile


---


20. Step 14 — History


Implement the history page.


Retrieve previous assessments for the logged-in user.


Display:


Date
Daily consumption
Weekly consumption
Monthly consumption
Water Saver Score


Allow users to understand changes over time.


Use charts for historical trends where appropriate.


---


21. Step 15 — AI Assistant


Create:


backend/services/ai_service.py


and the corresponding frontend interface.


The AI assistant should be able to answer questions related to:


- Water conservation
- The user's assessment
- Their consumption patterns
- Their recommendations
- Practical water-saving actions


The backend should construct the AI request.


Do not expose the AI API key in frontend JavaScript.


Use:


.env


for secrets.


---


22. AI Context


When appropriate, provide the AI with relevant structured information such as:


User type
Daily consumption
Major consumption categories
Water Saver Score
Existing recommendations


The AI should use this context to provide more relevant responses.


Do not send unnecessary personal information.


---


23. AI Safety and Reliability


The AI service must have fallback handling.


If:


- API key is missing
- API request fails
- API times out
- AI provider is unavailable


then the application should still function.


Display a helpful message and allow the user to continue using the rule-based recommendation system.


Never expose:


- API keys
- Internal errors
- Stack traces
- Sensitive backend information


to the user.


---


24. Step 16 — Gamification


Implement lightweight gamification after the core application works.


Include:


Current streak
Longest streak
Achievements
Badges


Possible achievements:


First Assessment
Water Saver
Consistency Champion
Improvement Milestone


The system should calculate achievements from actual user activity.


Do not make gamification more prominent than the actual conservation information.


---


25. Step 17 — API Implementation


Implement the API routes described in the Backend Schema Document.


Core endpoints include:


POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me


POST /api/assessments
GET  /api/assessments
GET  /api/assessments/<assessment_id>


GET /api/dashboard


GET /api/recommendations
GET /api/assessments/<assessment_id>/recommendations


POST /api/ai/chat


GET /api/profile
PUT /api/profile


Use consistent JSON responses.


Example successful response:


{
    "success": true,
    "data": {}
}


Example error:


{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Please provide a valid household size."
    }
}


---


26. Step 18 — Validation


Validate all user inputs on the backend even if frontend validation exists.


Check:


- Required fields
- Correct data types
- Reasonable ranges
- Valid user type
- Valid IDs
- Ownership
- Authentication


Never rely exclusively on client-side validation.


---


27. Step 19 — Error Handling


Implement user-friendly error handling.


The application should handle:


Invalid form input
Unauthenticated requests
Unauthorized requests
Missing database records
Database failures
AI service failures
Network failures
Unexpected server errors


Users should receive useful messages rather than technical stack traces.


---


28. Step 20 — Responsive Design


The entire application must work on:


Desktop
Tablet
Mobile


Pay particular attention to:


- Assessment forms
- Dashboard charts
- Sidebar
- Navigation
- AI chat
- Tables/history
- Cards


On smaller screens, the sidebar may become a collapsible navigation menu.


Charts must resize correctly.


---


29. Step 21 — UI Polish


After functionality is complete, refine the interface.


Add only purposeful:


- Hover effects
- Transitions
- Loading animations
- Progress indicators
- Success states
- Empty states


Avoid excessive animation.


Do not sacrifice performance for visual effects.


---


30. Step 22 — Testing


Create tests for important backend functionality.


Authentication


Test:


- Valid registration
- Duplicate email
- Invalid password
- Valid login
- Invalid login
- Logout


Calculations


Test:


- Valid household input
- Valid farmer input
- Different input ranges
- Missing values
- Invalid values
- Category totals
- Daily/weekly/monthly totals


Recommendations


Test:


- Low consumption
- High consumption
- Multiple triggered recommendations
- Recommendation priority


API


Test:


- Successful requests
- Invalid requests
- Unauthorized requests
- Missing resources


---


31. Step 23 — Complete End-to-End Test


Verify this complete flow:


New User
   ↓
Register
   ↓
Login
   ↓
Select Household/Farmer
   ↓
Complete Assessment
   ↓
Submit
   ↓
Calculate Consumption
   ↓
Generate Score
   ↓
Generate Recommendations
   ↓
Save Results
   ↓
Display Results
   ↓
Open Dashboard
   ↓
View History
   ↓
Open AI Assistant
   ↓
Ask Question
   ↓
Receive Response


The entire flow must work without manually modifying the database.


---


32. Step 24 — Security Requirements


Implement basic security practices.


Passwords


Never store plaintext passwords.


Environment variables


Keep secrets in:


.env


Never hard-code API keys.


Git


Never commit:


.env
*.db
passwords
API keys
secret tokens


Authorization


Users can only access their own:


- Assessments
- Results
- Recommendations
- AI conversations
- Profile
- Achievements


---


33. Step 25 — Seed/Demo Data


Provide an optional development/demo mechanism for creating sample data.


This may include:


- Sample household assessment
- Sample farmer assessment
- Sample recommendations
- Sample historical records


Demo data must be clearly separated from real user data.


Do not automatically populate fake data for normal production users.


---


34. Step 26 — README


Create a clear "README.md".


It should contain:


Project Overview
Features
Technology Stack
Project Structure
Installation
Environment Variables
How to Run
Database Setup
API Overview
AI Configuration
Testing
Troubleshooting


Include commands required to run the project locally.


---


35. Implementation Rules for the AI Coding Agent


While implementing AquaWise, follow these rules:


Rule 1


Do not delete existing functionality without a clear reason.


Rule 2


Before modifying a file, understand how it is currently used.


Rule 3


Reuse existing components instead of creating duplicates.


Rule 4


Keep frontend and backend responsibilities separate.


Rule 5


Keep calculations deterministic.


Rule 6


Do not hard-code secrets.


Rule 7


Do not expose backend API keys to the frontend.


Rule 8


Validate backend input.


Rule 9


Protect user-owned data.


Rule 10


Keep the application usable if AI is unavailable.


Rule 11


Do not create unnecessary dependencies.


Rule 12


Do not replace working architecture with a completely different framework unless explicitly instructed.


Rule 13


Test important functionality after implementation.


Rule 14


Keep code readable for beginner developers who need to understand and explain it.


Rule 15


If a requirement is ambiguous, choose the simplest implementation consistent with the existing project documents.


---


36. Priority System


When implementing features, use this priority order.


Priority 1 — Core functionality


Authentication
Assessment
Database
Calculation
Results
Recommendations
Dashboard


Priority 2 — Tracking


History
Comparison
Water Saver Score


Priority 3 — AI


AI Assistant
AI personalization


Priority 4 — Enhancement


Achievements
Streaks
Animations
Additional visual polish


Do not delay the core application because of enhancement features.


---


37. Final Architecture


The final system should conceptually work like this:


                    AQUAWISE
                       │
        ┌──────────────┴──────────────┐
        │                             │
    FRONTEND                      FLASK API
        │                             │
        │                    ┌────────┴────────┐
        │                    │                 │
        │               SERVICES           DATABASE
        │                    │                 │
        │          ┌─────────┼─────────┐       │
        │          │         │         │       │
        │     Calculation Recommendation AI     │
        │          │         │         │