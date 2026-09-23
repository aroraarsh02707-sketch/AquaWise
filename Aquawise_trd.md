AQUAWISE


Technical Requirements Document (TRD)


Project: AquaWise — Water Conservation Recommendation System
Project Type: Environmental Studies / CA Group Project
Application Type: Full-stack Web Application
Target Users: General Public, Household Users, Farmers
Team Size: 3 Members
Document Version: 1.0
Status: Development Specification


---


1. PURPOSE OF THIS DOCUMENT


This Technical Requirements Document defines the technical architecture, technologies, software components, data structures, APIs, security requirements, AI integration, development workflow, and deployment requirements for AquaWise.


This document should be used together with the AquaWise Project Requirements Document.


The Project Requirements Document defines what the application must accomplish.


This document defines how the application should technically accomplish it.


An AI development agent should use this document as the technical implementation specification.


---


2. TECHNICAL OBJECTIVE


AquaWise must be implemented as a modular full-stack web application capable of:


1. Collecting household and agricultural water-use data.
2. Validating user input.
3. Calculating estimated water consumption.
4. Categorizing consumption by activity.
5. Identifying high-consumption activities.
6. Generating personalized recommendations.
7. Using AI for recommendation personalization and conversational assistance.
8. Storing assessment history.
9. Displaying historical trends.
10. Providing weekly and monthly comparisons.
11. Providing a responsive and visually appealing dashboard.
12. Maintaining secure user accounts.
13. Operating even when the AI service is temporarily unavailable.


---


3. RECOMMENDED TECHNOLOGY STACK


The initial implementation should use the following stack.


Frontend


- HTML5
- CSS3
- JavaScript (ES6+)
- Chart.js


Backend


- Python 3
- Flask


Database


- SQLite
- SQLAlchemy


Authentication


- Flask-Login or equivalent lightweight authentication system
- Werkzeug password hashing


AI


- External LLM API through the backend
- Provider should be configurable through environment variables


Version Control


- Git
- GitHub


Development Environment


- Visual Studio Code
- Python virtual environment ("venv")


---


4. ARCHITECTURE


AquaWise should use a layered architecture.


                    USER
                     │
                     ▼
             ┌───────────────┐
             │   FRONTEND    │
             │ HTML/CSS/JS   │
             └───────┬───────┘
                     │
                HTTP / JSON
                     │
                     ▼
             ┌───────────────┐
             │ FLASK BACKEND │
             │   REST API    │
             └───────┬───────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
   Calculation   Recommendation  AI
     Engine          Engine      Service
          │          │          │
          └──────────┼──────────┘
                     │
                     ▼
             ┌───────────────┐
             │   DATABASE    │
             │    SQLite     │
             └───────────────┘


---


5. APPLICATION LAYERS


5.1 Presentation Layer


Responsible for:


- UI
- Forms
- Navigation
- Dashboard
- Charts
- User interaction
- Responsive design


Technology:


HTML
CSS
JavaScript
Chart.js


---


5.2 API / Backend Layer


Responsible for:


- Authentication
- Request handling
- Input validation
- Business logic
- Database communication
- Calculation requests
- Recommendation requests
- AI requests


Technology:


Python
Flask


---


5.3 Business Logic Layer


Responsible for:


- Water consumption calculations
- Daily/weekly/monthly conversions
- Usage categorization
- High-consumption detection
- Water Saver Score
- Recommendation selection


This logic should not be placed directly inside HTML or frontend JavaScript.


---


5.4 Data Layer


Responsible for:


- User data
- Assessment records
- Usage breakdowns
- Recommendations
- AI conversation history


Technology:


SQLite
SQLAlchemy


---


6. PROJECT DIRECTORY STRUCTURE


Recommended structure:


AquaWise/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── frontend/
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── assessment.html
│   │   ├── results.html
│   │   ├── dashboard.html
│   │   ├── history.html
│   │   ├── profile.html
│   │   └── assistant.html
│   │
│   └── static/
│       ├── css/
│       │   ├── style.css
│       │   ├── dashboard.css
│       │   └── forms.css
│       │
│       ├── js/
│       │   ├── main.js
│       │   ├── assessment.js
│       │   ├── dashboard.js
│       │   ├── history.js
│       │   └── assistant.js
│       │
│       └── assets/
│           ├── images/
│           └── icons/
│
├── backend/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── assessment.py
│   │   ├── dashboard.py
│   │   └── assistant.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── assessment.py
│   │   ├── usage.py
│   │   └── recommendation.py
│   │
│   ├── services/
│   │   ├── calculation_service.py
│   │   ├── recommendation_service.py
│   │   ├── ai_service.py
│   │   └── scoring_service.py
│   │
│   └── utils/
│       ├── validators.py
│       └── constants.py
│
├── database/
│   └── aquawise.db
│
└── tests/
    ├── test_calculations.py
    ├── test_validation.py
    ├── test_auth.py
    └── test_recommendations.py


The AI development agent may simplify this structure if the resulting architecture remains modular and maintainable.


---


7. FRONTEND REQUIREMENTS


7.1 General


The frontend must:


- Be responsive.
- Work on mobile and desktop.
- Use semantic HTML.
- Maintain consistent styling.
- Provide accessible form labels.
- Display clear validation messages.
- Avoid unnecessary page reloads where practical.


---


8. FRONTEND PAGES


8.1 Landing Page


Route:


/


Must contain:


- AquaWise branding
- Hero section
- Project explanation
- Start Assessment button
- Household/Farmer introduction
- How it works
- Benefits
- AI assistant introduction
- Footer


---


8.2 Registration


Route:


/register


Fields:


name
email
password
confirm_password
user_type


Validation must occur both client-side and server-side.


---


8.3 Login


Route:


/login


Fields:


email
password


---


8.4 Assessment


Route:


/assessment


The form should dynamically display:


Household Assessment


or:


Farmer Assessment


based on user selection.


---


8.5 Results


Route:


/results/<assessment_id>


Display:


- Daily consumption
- Weekly equivalent
- Monthly equivalent
- Activity breakdown
- Highest usage category
- Water Saver Score
- Recommendations


---


8.6 Dashboard


Route:


/dashboard


Display:


- Current consumption
- Historical consumption
- Charts
- Water Saver Score
- Recommendations
- Comparison information


---


8.7 History


Route:


/history


Display:


- Previous assessments
- Assessment date
- Consumption
- Score
- View button


---


8.8 AI Assistant


Route:


/assistant


Provide:


- Chat interface
- User message input
- AI response area
- Conversation history where implemented


---


9. FORM INPUT SPECIFICATION


Household Assessment


Required fields:


household_size
showers_per_day
average_shower_duration
toilet_flushes_per_day
laundry_loads_per_week
dishwashing_frequency
vehicle_washing_frequency
gardening_frequency
gardening_duration


Optional fields:


bathing_method
dishwashing_method
vehicle_washing_method
gardening_method
other_water_usage


---


Farmer Assessment


Required fields:


farm_area
crop_type
irrigation_frequency
irrigation_duration
irrigation_method
water_source


Optional:


estimated_water_per_irrigation
location
rainfall_information


---


10. DATA TYPES


Recommended types:


Field| Type
Name| String
Email| String
Password| String
Household Size| Integer
Duration| Float
Frequency| Integer/Float
Farm Area| Float
Consumption| Float
Score| Integer
Date| DateTime
User Type| Enum/String


All numeric inputs must be validated to ensure they are within reasonable ranges.


---


11. DATABASE SCHEMA


11.1 Users


users
-----
id
name
email
password_hash
user_type
created_at
updated_at


Constraints:


- "id" = primary key
- "email" = unique
- "password_hash" = required
- "user_type" = household/farmer


---


11.2 Assessments


assessments
-----------
id
user_id
assessment_date
daily_consumption
weekly_consumption
monthly_consumption
water_score
created_at


Relationship:


User 1 ──────── * Assessments


---


11.3 Usage Details


usage_details
-------------
id
assessment_id
category
consumption
percentage


Example categories:


bathing
toilet
laundry
kitchen
vehicle
gardening
irrigation
other


---


11.4 Recommendations


recommendations
---------------
id
assessment_id
category
title
description
potential_saving
source_type
created_at


"source_type" can contain:


rule
ai
hybrid


---


11.5 AI Conversations


ai_conversations
----------------
id
user_id
assessment_id
user_message
ai_response
created_at


---


12. DATABASE RELATIONSHIPS


User
 │
 ├────── Assessments
 │            │
 │            ├──── Usage Details
 │            │
 │            └──── Recommendations
 │
 └────── AI Conversations


---


13. WATER CALCULATION ENGINE


The calculation engine must be implemented as an independent Python service.


File:


backend/services/calculation_service.py


It should accept structured input and return structured results.


Example conceptual interface:


calculate_household_usage(data)


and:


calculate_farmer_usage(data)


---


14. CALCULATION MODEL


The system should use configurable assumptions.


Example:


daily_shower_usage =
showers_per_day × shower_duration × flow_rate


For weekly activities:


daily_laundry_usage =
weekly_laundry_usage / 7


For monthly estimates:


monthly_usage =
daily_usage × 30


For weekly estimates:


weekly_usage =
daily_usage × 7


These are estimates, not direct measurements.


---


15. CONFIGURATION OF WATER ASSUMPTIONS


Store assumptions centrally.


Example:


WATER_ASSUMPTIONS = {
    "shower_flow_rate": ...,
    "toilet_flush_volume": ...,
    "laundry_per_load": ...,
    "dishwashing_rate": ...,
    "vehicle_wash_volume": ...,
    "garden_water_rate": ...
}


Exact assumption values should be based on credible references selected during implementation.


The values must be easy to change without modifying the calculation logic.


---


16. CALCULATION OUTPUT


The calculation service should return an object similar to:


{
  "daily_consumption": 385,
  "weekly_consumption": 2695,
  "monthly_consumption": 11550,
  "breakdown": {
    "bathing": 120,
    "toilet": 60,
    "laundry": 55,
    "kitchen": 70,
    "gardening": 40,
    "vehicle": 20,
    "other": 20
  }
}


Actual values depend on user input.


---


17. RECOMMENDATION ENGINE


File:


backend/services/recommendation_service.py


The recommendation engine should combine:


1. Rule-based detection
2. Personalized AI generation


The rule-based component determines which categories require attention.


Example:


if bathing_usage > threshold:
    recommendations.append("bathing")


AI may then convert relevant categories and user information into natural-language recommendations.


---


18. RECOMMENDATION OUTPUT FORMAT


The backend should return structured recommendations.


Example:


{
  "category": "bathing",
  "title": "Reduce Shower Duration",
  "description": "Reducing shower duration can lower water consumption.",
  "potential_saving": 30,
  "source_type": "hybrid"
}


---


19. AI SERVICE


File:


backend/services/ai_service.py


The AI service should act as a separate abstraction layer.


The rest of the application should not directly call an external AI API.


Architecture:


Flask
  ↓
AI Service
  ↓
LLM API


This makes it possible to replace the AI provider later.


---


20. AI CONFIGURATION


AI credentials must be stored in environment variables.


Example:


AI_API_KEY=your_key_here
AI_MODEL=selected_model


Never hard-code credentials.


The ".env" file must be included in ".gitignore".


A safe example file should be provided:


.env.example


Example:


AI_API_KEY=
AI_MODEL=
SECRET_KEY=
DATABASE_URL=


---


21. AI PROMPT STRUCTURE


The backend should provide structured context to the AI.


Example:


User Type: Household


Household Size: 4


Estimated Daily Consumption: 385 L


Highest Usage Categories:
- Bathing
- Kitchen


User Habits:
- 3 showers/day
- 10 minute average shower
- Frequent gardening


Task:
Generate 3 practical water conservation recommendations.


Requirements:
- Be concise.
- Base recommendations only on supplied information.
- Do not claim estimates are exact.
- Avoid unsafe advice.
- Prioritize practical actions.


The actual prompt should be maintained in a dedicated prompt file where practical.


---


22. AI FAILURE FALLBACK


If the AI API fails:


AI Request
    ↓
Failure
    ↓
Rule-Based Recommendation Engine
    ↓
Return recommendations


The application must not crash because of an AI failure.


The user should see something like:


«"AI recommendations are temporarily unavailable. Here are recommendations based on your water-use profile."»


---


23. AI ASSISTANT API


Recommended endpoint:


POST /api/assistant/chat


Request:


{
  "message": "How can I reduce water usage while gardening?"
}


Response:


{
  "response": "..."
}


The backend should optionally include the user's current assessment context.


---


24. REST API


Recommended API structure:


Authentication


POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me


Assessment


POST /api/assessments
GET  /api/assessments
GET  /api/assessments/<id>


Dashboard


GET /api/dashboard
GET /api/dashboard/trends


Recommendations


GET /api/assessments/<id>/recommendations


AI


POST /api/assistant/chat
GET  /api/assistant/history


---


25. API RESPONSE FORMAT


Responses should use JSON.


Success example:


{
  "success": true,
  "data": {}
}


Error example:


{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Household size must be greater than zero."
  }
}


---


26. HTTP STATUS CODES


Use appropriate HTTP status codes.


200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
500 Internal Server Error
503 Service Unavailable


---


27. AUTHENTICATION & AUTHORIZATION


Users must authenticate before accessing private information.


Protected resources include:


/dashboard
/history
/profile
/api/assessments
/api/assistant/history


A user must only be able to retrieve their own records.


Example:


User A
  ↓
GET /api/assessments/25


If Assessment 25 belongs to User B:
→ Return 403 or 404


---


28. PASSWORD SECURITY


Passwords must never be stored directly.


Use:


Werkzeug password hashing


Conceptually:


generate_password_hash(password)
check_password_hash(hash, password)


---


29. INPUT VALIDATION


Validation must occur at two levels:


Frontend


Provides immediate feedback.


Backend


Provides authoritative validation.


The backend must never trust frontend validation.


---


30. EXAMPLE VALIDATION RULES


household_size >= 1


showers_per_day >= 0


shower_duration >= 0


laundry_loads_per_week >= 0


farm_area > 0


irrigation_frequency >= 0


irrigation_duration >= 0


Maximum values should also be defined to prevent unreasonable inputs.


---


31. SECURITY REQUIREMENTS


The application must:


- Hash passwords.
- Validate all input.
- Use parameterized database queries.
- Protect private routes.
- Keep API keys server-side.
- Prevent users from accessing other users' data.
- Use secure session configuration.
- Avoid exposing stack traces in production.


---


32. ENVIRONMENT VARIABLES


Sensitive configuration should be stored using environment variables.


Required variables:


SECRET_KEY
DATABASE_URL
AI_API_KEY
AI_MODEL


Optional:


DEBUG


Production credentials must not be stored in GitHub.


---


33. GIT REQUIREMENTS


The Git repository must include:


.gitignore
README.md
requirements.txt
.env.example


The following must NOT be committed:


.env
*.db
__pycache__/
venv/
.venv/


unless the database is intentionally included as a demonstration artifact.


---


34. BRANCHING STRATEGY


For a 3-person beginner team, keep Git workflow simple.


Recommended:


main
│
├── frontend
├── backend
└── ai


Each member works on their assigned branch.


Changes should be merged into "main" after basic testing.


Avoid directly making large experimental changes to "main".


---


35. TEAM TECHNICAL RESPONSIBILITIES


Member 1 — Frontend


Responsible for:


HTML
CSS
JavaScript
Dashboard
Charts
Responsive design
Frontend validation


---


Member 2 — Backend


Responsible for:


Flask
REST API
Database
Authentication
Calculation engine
Backend validation


---


Member 3 — AI


Responsible for:


Recommendation engine
AI service
AI prompts
AI assistant
AI fallback system
AI testing


All members should understand the interfaces between their components.


---


36. CHART IMPLEMENTATION


Use Chart.js.


Required visualizations:


Activity Breakdown


Recommended:


Doughnut Chart


Historical Consumption


Recommended:


Line Chart


Category Comparison


Recommended:


Bar Chart


Charts must receive data dynamically from the backend rather than containing hard-coded final results.


---


37. DASHBOARD DATA FLOW


User Login
    ↓
Dashboard Request
    ↓
GET /api/dashboard
    ↓
Flask
    ↓
Database
    ↓
Historical Assessments
    ↓
JSON Response
    ↓
JavaScript
    ↓
Chart.js
    ↓
Visual Dashboard


---


38. RESPONSIVE DESIGN


Use CSS media queries.


The application should support:


Mobile: approximately 320px+
Tablet: approximately 768px+
Desktop: approximately 1024px+


The UI should not require horizontal scrolling on normal devices.


---


39. ACCESSIBILITY


Use:


- Semantic HTML
- "<label>" for form controls
- Descriptive buttons
- Keyboard-accessible navigation
- Adequate text contrast
- Alternative text for meaningful images
- Clear form error messages


Do not rely solely on color to communicate important information.


---


40. PERFORMANCE REQUIREMENTS


The application should:


- Load normal pages quickly.
- Avoid unnecessary API requests.
- Avoid loading unnecessarily large images.
- Keep frontend JavaScript modular.
- Query only necessary database records.
- Avoid generating AI responses for operations that do not require AI.


---


41. LOGGING


Backend errors should be logged.


Logs may include:


timestamp
route
error type
error message
request ID


Logs must not expose:


- Passwords
- API keys
- Sensitive user information


---


42. TESTING


Testing should be performed at multiple levels.


Unit Testing


Test:


- Water calculations
- Score calculations
- Validation
- Recommendation rules


---


Integration Testing


Test:


Frontend → API → Backend → Database


and:


Backend → AI Service


---


User Flow Testing


Test complete flows:


Register
↓
Login
↓
Assessment
↓
Calculation
↓
Results
↓
Save
↓
Dashboard
↓
History


---


43. TEST CASE EXAMPLES


Test Case 1


Input:


Household size = 4
Showers = 2/day
Duration = 5 minutes


Expected:


Valid input


---


Test Case 2


Input:


Household size = -2


Expected:


Validation error


---


Test Case 3


User submits assessment.


Expected:


Assessment stored in database.


---


Test Case 4


AI API unavailable.


Expected:


Application continues working using rule-based recommendations.


---


Test Case 5


User attempts to access another user's assessment.


Expected:


Access denied.


---


44. DEPLOYMENT


The application should be deployable to a cloud platform supporting Python/Flask.


The exact hosting provider can be selected later.


Production deployment should include:


Python runtime
Flask application
Database
Environment variables
HTTPS


Development and production configurations should be separated.


---


45. DATABASE MIGRATION


If the project later moves from SQLite to PostgreSQL, the application architecture should allow the database URL to be changed through configuration rather than requiring major code changes.


Example:


DATABASE_URL


---


46. DOCUMENTATION REQUIREMENTS


The GitHub