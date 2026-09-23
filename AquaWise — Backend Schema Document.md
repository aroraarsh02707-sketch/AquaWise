AquaWise — Backend Schema Document


1. Document Purpose


This document defines the backend data structure and database schema for AquaWise — Water Conservation Recommendation System.


It specifies:


- Database tables
- Fields and data types
- Primary and foreign keys
- Relationships between tables
- Assessment data structure
- Water-consumption data
- Recommendations
- AI conversations
- Achievements and streaks
- API data structures
- Validation requirements
- Data flow between frontend, backend, calculation services, AI services, and database


This document should be treated as the backend data blueprint for the AquaWise development team and AI coding agents.


---


2. Backend Architecture


The backend should follow a layered architecture:


Frontend
   ↓
Flask Routes / API
   ↓
Validation
   ↓
Service Layer
   ├── Calculation Service
   ├── Recommendation Service
   ├── Scoring Service
   └── AI Service
   ↓
Database Models
   ↓
SQLite Database


The backend is responsible for:


1. Receiving user input
2. Validating input
3. Calculating water consumption
4. Generating recommendations
5. Generating conservation scores
6. Storing assessment results
7. Maintaining user history
8. Tracking streaks and achievements
9. Providing dashboard data
10. Communicating with the AI service


---


3. Database Technology


Recommended Database


SQLite


Reason:


- Simple to configure
- Suitable for the project's MVP
- No separate database server required
- Easy local development
- Works well with Flask
- Easy to migrate to PostgreSQL later


ORM


Use:


SQLAlchemy


The application should interact with database models through SQLAlchemy rather than writing raw SQL throughout the application.


---


4. Database Naming Convention


Use:


- "snake_case" for table names
- "snake_case" for column names
- Singular model names in Python
- Plural table names where appropriate


Examples:


User
Assessment
UsageDetail
Recommendation
AIConversation
Achievement


Database tables:


users
assessments
usage_details
recommendations
ai_conversations
achievements
user_achievements
streaks


---


5. Entity Relationship Overview


The main relationship structure is:


USER
 │
 ├───────────────┐
 ↓               ↓
ASSESSMENTS      STREAK
 │
 ↓
USAGE_DETAILS
 │
 ├──────────────→ RECOMMENDATIONS
 │
 ↓
SCORE / RESULTS
 │
 ↓
DASHBOARD


AI interaction:


USER
 │
 ↓
AI_CONVERSATIONS
 │
 ↓
AI_MESSAGES


Achievement system:


USER
 │
 ↓
USER_ACHIEVEMENTS
 │
 ↓
ACHIEVEMENTS


---


6. Users Table


Table: "users"


Stores account and basic profile information.


Field| Type| Constraints| Description
id| Integer| Primary Key| Unique user ID
name| String| Required| User's name
email| String| Required, Unique| User email
password_hash| String| Required| Hashed password
user_type| String| Required| household / farmer
created_at| DateTime| Required| Account creation time
updated_at| DateTime| Required| Last profile update
is_active| Boolean| Default True| Account status


Important


Never store plain-text passwords.


Passwords must be hashed using a secure password hashing mechanism such as Werkzeug's password hashing utilities.


---


7. User Type


The "user_type" field should contain one of:


household
farmer


The backend should reject unsupported values.


---


8. Assessments Table


Table: "assessments"


Stores each water-consumption assessment completed by a user.


A user can have multiple assessments.


Field| Type| Constraints| Description
id| Integer| Primary Key| Assessment ID
user_id| Integer| Foreign Key| Owner
assessment_type| String| Required| household / farmer
assessment_date| DateTime| Required| Date of assessment
daily_consumption| Float| Required| Estimated litres/day
weekly_consumption| Float| Required| Estimated litres/week
monthly_consumption| Float| Required| Estimated litres/month
water_saver_score| Integer| Required| Score
created_at| DateTime| Required| Record creation


Relationship:


User 1 ──────── * Assessments


One user can have many assessments.


---


9. Household Usage Details


Table: "household_usage_details"


Stores household-specific assessment information.


Field| Type| Description
id| Integer| Primary Key
assessment_id| Integer| Related assessment
household_size| Integer| Number of people
showers_per_day| Float| Showers/baths per day
shower_duration_minutes| Float| Average duration
toilet_uses_per_day| Float| Estimated usage
laundry_loads_per_week| Float| Laundry frequency
kitchen_usage_minutes| Float| Kitchen/dishwashing usage
vehicle_washing_frequency| Float| Vehicle washing frequency
gardening_frequency| Float| Gardening frequency
gardening_duration_minutes| Float| Gardening duration
other_usage_litres| Float| Additional estimated usage


Relationship:


Assessment 1 ──────── 0/1 HouseholdUsageDetails


Only household assessments should have a household usage record.


---


10. Farmer Usage Details


Table: "farmer_usage_details"


Stores agricultural water-use information.


Field| Type| Description
id| Integer| Primary Key
assessment_id| Integer| Related assessment
farm_area| Float| Farm area
farm_area_unit| String| acre / hectare / other
crop_type| String| Main crop
irrigation_method| String| Irrigation method
irrigation_frequency| Float| Irrigation sessions
irrigation_duration_minutes| Float| Duration
water_source| String| Main water source
rainfall_information| String| Rainfall information
rainwater_harvesting| Boolean| Availability/use
estimated_irrigation_litres| Float| Estimated water usage


Possible irrigation methods:


flood
drip
sprinkler
other


Possible water sources:


groundwater
canal
rainwater
tank
other


---


11. Usage Details Design


Household and farmer data should remain separated because their inputs and calculations are different.


Do not create one extremely large table containing every possible household and agricultural field.


Recommended structure:


assessments
    │
    ├── household_usage_details
    │
    └── farmer_usage_details


This keeps the database easier to understand and maintain.


---


12. Consumption Breakdown Table


Table: "consumption_breakdowns"


Stores the calculated water usage for individual categories.


Field| Type| Description
id| Integer| Primary Key
assessment_id| Integer| Related assessment
category| String| Usage category
litres_per_day| Float| Estimated daily usage
percentage| Float| Percentage of total


Example records:


Bathroom       150 L/day
Kitchen         80 L/day
Laundry         70 L/day
Gardening       60 L/day
Vehicle         60 L/day


Relationship:


Assessment 1 ──────── * ConsumptionBreakdown


This allows the dashboard to generate charts dynamically.


---


13. Recommendation Table


Table: "recommendations"


Stores recommendations generated for a specific assessment.


Field| Type| Description
id| Integer| Primary Key
assessment_id| Integer| Related assessment
category| String| Relevant usage category
title| String| Recommendation title
description| Text| Recommendation explanation
priority| String| low / medium / high
source| String| rule_based / ai
created_at| DateTime| Creation time


Example:


Category: Gardening
Title: Improve irrigation efficiency
Priority: High
Source: rule_based


---


14. Recommendation Generation


The backend should use a hybrid system.


Assessment Data
      ↓
Calculation Service
      ↓
Usage Breakdown
      ↓
Rule-Based Recommendation Engine
      ↓
Optional AI Personalization
      ↓
Recommendations


Rule-based logic should generate the core recommendations.


AI can then personalize the wording or provide additional contextual suggestions.


---


15. Recommendation Priority


Use:


low
medium
high


Priority should be determined from predefined backend rules.


For example:


High:
Significant usage or clear conservation opportunity


Medium:
Moderate opportunity


Low:
General improvement suggestion


Do not allow the AI model to arbitrarily assign priority without validation.


---


16. AI Conversations Table


Table: "ai_conversations"


Stores conversations between a user and the AquaWise AI assistant.


Field| Type| Description
id| Integer| Primary Key
user_id| Integer| User
created_at| DateTime| Conversation creation
updated_at| DateTime| Last activity


Relationship:


User 1 ──────── * AIConversations


---


17. AI Messages Table


Table: "ai_messages"


Stores individual messages.


Field| Type| Description
id| Integer| Primary Key
conversation_id| Integer| Conversation
role| String| user / assistant
message| Text| Message content
created_at| DateTime| Timestamp


Relationship:


AIConversation 1 ──────── * AIMessages


---


18. AI Data Privacy


Only relevant information should be sent to the AI service.


For example:


User Type
Daily Consumption
Major Usage Categories
Relevant Assessment Data


Do not send:


- Passwords
- Password hashes
- Authentication tokens
- Unnecessary personal information
- Database credentials
- API keys


---


19. Achievements Table


Table: "achievements"


Stores available achievement definitions.


Field| Type| Description
id| Integer| Primary Key
name| String| Achievement name
description| Text| Achievement explanation
icon| String| Icon identifier
requirement_type| String| Requirement category
requirement_value| Float| Required value


Example:


First Assessment
Consistent Saver
Water Watcher
Conservation Milestone


---


20. User Achievements Table


Table: "user_achievements"


Connects users with achievements they have earned.


Field| Type| Description
id| Integer| Primary Key
user_id| Integer| User
achievement_id| Integer| Achievement
earned_at| DateTime| Date earned


Relationship:


User * ──────── * Achievement


This is implemented using the "user_achievements" table.


---


21. Streaks Table


Table: "streaks"


Stores user conservation streak information.


Field| Type| Description
id| Integer| Primary Key
user_id| Integer| User
current_streak| Integer| Current streak
longest_streak| Integer| Longest streak
last_activity_date| Date| Last qualifying activity
updated_at| DateTime| Last update


Relationship:


User 1 ──────── 1 Streak


---


22. Streak Logic


The streak system should be handled by deterministic backend logic.


Example:


User completes qualifying activity today
        ↓
Check last activity date
        ↓
If consecutive → current_streak + 1
        ↓
If not consecutive → reset or start new streak
        ↓
Update longest_streak if necessary


The exact definition of a "qualifying activity" should be configurable.


Possible qualifying activities:


- Completing an assessment
- Updating water usage
- Completing a conservation action


---


23. Dashboard Data Model


The dashboard does not require a separate "dashboard" table.


Dashboard data should be generated from existing records.


Flow:


User
 ↓
Latest Assessment
 ↓
Consumption Breakdown
 ↓
Recommendations
 ↓
Streak
 ↓
Achievements
 ↓
Historical Assessments
 ↓
Dashboard Response


This avoids unnecessary duplicated data.


---


24. Dashboard API Response


Example:


{
  "daily_consumption": 420,
  "weekly_consumption": 2940,
  "monthly_consumption": 12600,
  "water_saver_score": 72,
  "current_streak": 7,
  "top_category": "Bathroom",
  "latest_recommendation": {
    "title": "Reduce unnecessary water use",
    "category": "Bathroom"
  }
}


The frontend should use this response to construct the dashboard.


---


25. Assessment API


Create Assessment


POST /api/assessments


Example household request:


{
  "assessment_type": "household",
  "household_size": 4,
  "showers_per_day": 4,
  "shower_duration_minutes": 8,
  "toilet_uses_per_day": 16,
  "laundry_loads_per_week": 5,
  "kitchen_usage_minutes": 30,
  "vehicle_washing_frequency": 1,
  "gardening_frequency": 3
}


The backend should:


1. Validate data
2. Create assessment
3. Calculate consumption
4. Generate breakdown
5. Calculate score
6. Generate recommendations
7. Save results
8. Return results


---


26. Assessment Response


Example:


{
  "assessment_id": 25,
  "daily_consumption": 420,
  "weekly_consumption": 2940,
  "monthly_consumption": 12600,
  "water_saver_score": 72,
  "breakdown": [
    {
      "category": "Bathroom",
      "litres_per_day": 150,
      "percentage": 35.7
    },
    {
      "category": "Kitchen",
      "litres_per_day": 80,
      "percentage": 19.0
    }
  ],
  "recommendations": [
    {
      "title": "Reduce unnecessary water use",
      "category": "Bathroom",
      "priority": "medium"
    }
  ]
}


---


27. History API


Get User History


GET /api/assessments


Response:


{
  "assessments": [
    {
      "id": 25,
      "date": "2026-09-23",
      "daily_consumption": 420,
      "water_saver_score": 72
    },
    {
      "id": 20,
      "date": "2026-09-15",
      "daily_consumption": 460,
      "water_saver_score": 68
    }
  ]
}


The frontend can use this information to create the History page.


---


28. Detailed Assessment API


Get Specific Assessment


GET /api/assessments/<assessment_id>


The response should include:


- Assessment information
- Usage details
- Consumption breakdown
- Score
- Recommendations
- Date


The backend must verify that the requested assessment belongs to the authenticated user.


---


29. Dashboard API


GET /api/dashboard


The response should contain:


- Latest consumption
- Weekly consumption
- Monthly consumption
- Score
- Streak
- Top usage category
- Recent recommendations
- Recent history
- Achievement summary


---


30. Recommendations API


GET /api/recommendations


Optional:


GET /api/assessments/<assessment_id>/recommendations


The API should return recommendations associated with the authenticated user.


---


31. AI Assistant API


Send Message


POST /api/ai/chat


Example request:


{
  "conversation_id": 5,
  "message": "How can I reduce my water usage?"
}


Backend flow:


Request
 ↓
Authentication
 ↓
Input Validation
 ↓
Retrieve Relevant User Context
 ↓
Create AI Prompt
 ↓
AI Service
 ↓
Validate Response
 ↓
Save Message
 ↓
Return Response


---


32. Profile API


Possible endpoints:


GET /api/profile
PUT /api/profile


The user can update permitted profile fields.


The backend should not allow users to modify protected fields directly without appropriate validation.


---


33. Authentication API


Register


POST /api/auth/register


Login


POST /api/auth/login


Logout


POST /api/auth/logout


Current User


GET /api/auth/me


---


34. API Authentication


All protected API endpoints should require an authenticated user.


Protected examples:


/api/dashboard
/api/assessments
/api/recommendations
/api/history
/api/ai/chat
/api/profile


Public examples:


/api/auth/register
/api/auth/login


---


35. Authorization Rules


A user must only be able to access their own data.


For example:


User A
 ↓
Assessment 10


User B must not be able to request:


GET /api/assessments/10


and receive User A's data.


The backend must verify ownership before returning records.


---


36. Input Validation


Validation should happen on the backend even if frontend validation already exists.


Validate:


- Required fields
- Data types
- Numeric ranges
- Allowed enum values
- String lengths
- Email format
- Password requirements
- Assessment ownership
- IDs


Never trust frontend validation alone.


---


37. Example Numeric Validation


Example:


household_size > 0
showers_per_day >= 0
shower_duration_minutes >= 0
laundry_loads_per_week >= 0
farm_area > 0
irrigation_frequency >= 0


The exact maximum limits should be defined in backend constants.


---


38. Calculation Service


The calculation service should be independent from Flask routes.


Recommended file:


backend/services/calculation_service.py


Example structure:


calculate_household_consumption(data)


calculate_farmer_consumption(data)


calculate_daily_consumption(data)


calculate_weekly_consumption(daily)


calculate_monthly_consumption(daily)


Routes should call these functions rather than containing calculation formulas directly.


---


39. Recommendation Service


Recommended file:


backend/services/recommendation_service.py


Responsibilities:


- Analyze usage breakdown
- Identify high-usage categories
- Apply recommendation rules
- Assign priority
- Generate recommendation records
- Pass relevant context to AI when required


---


40. Scoring Service


Recommended file:


backend/services/scoring_service.py


Responsibilities:


- Calculate Water Saver Score
- Apply predefined scoring rules
- Keep scoring consistent
- Return a score between the defined minimum and maximum


Example:


0 ≤ score ≤ 100


The scoring system should be deterministic.


---


41. AI Service


Recommended file:


backend/services/ai_service.py


Responsibilities:


- Communicate with external AI API
- Construct prompts
- Provide relevant assessment context
- Handle API errors
- Apply timeout limits
- Return safe structured responses


The AI API key must be stored in environment variables.


Example:


AI_API_KEY=your_key_here


Never commit API keys to GitHub.


---


42. Configuration


Sensitive configuration should use environment variables.


Example ".env":


SECRET_KEY=...
DATABASE_URL=...
AI_API_KEY=...
AI_MODEL=...


A ".env.example" file should contain placeholder values.


The real ".env" file must be included in ".gitignore".


---


43. Error Response Format


All APIs should use a consistent error format.


Example:


{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please enter a valid household size."
  }
}


Successful responses can follow:


{
  "success": true,
  "data": {}
}


---


44. HTTP Status Codes


Use standard HTTP status codes.


Code| Meaning
200| Successful request
201| Resource created
400| Invalid request
401| Not authenticated
403| Not authorized
404| Resource not found
409| Conflict
422| Validation error
500| Server error


---


45. Database Relationships Summary


USERS
 │
 ├──< ASSESSMENTS
 │       │
 │       ├──< CONSUMPTION_BREAKDOWNS
 │       │
 │       ├──< RECOMMENDATIONS
 │       │
 │       ├── HOUSEHOLD_USAGE_DETAILS
 │       │
 │       └── FARMER_USAGE_DETAILS
 │
 ├── STREAKS
 │
 ├──< AI_CONVERSATIONS
 │       │
 │       └──< AI_MESSAGES
 │
 └──< USER_ACHIEVEMENTS >── ACHIEVEMENTS


---


46. Data Lifecycle


Assessment Lifecycle


User enters data
        ↓
Frontend validation
        ↓
Backend validation
        ↓
Assessment created
        ↓
Consumption calculated
        ↓
Breakdown generated
        ↓
Score calculated
        ↓
Recommendations generated
        ↓
Results stored
        ↓
Dashboard updated
        ↓
History updated


---


47. Deletion Rules


Assessment data should not be deleted accidentally.


If an assessment is deleted, related records should be handled consistently.


Recommended relationship behavior:


Assessment deleted
       ↓
Delete related:
- Usage details
- Consumption breakdowns
- Recommendations


AI conversations and user achievements should be handled separately.


For the MVP, hard deletion can be used where appropriate, but cascading relationships must be configured carefully.


---


48. Database Indexing


Indexes should be added to frequently queried fields.


Recommended indexes:


users.email
assessments.user_id
assessments.assessment_date
recommendations.assessment_id
ai_conversations.user_id
ai_messages.conversation_id
user_achievements.user_id


The email field must have a uniqueness constraint.


---


49. Security Requirements


The backend must:


- Hash passwords
- Protect authenticated routes
- Validate all input
- Verify resource ownership
- Protect API keys
- Avoid exposing sensitive database information
- Use secure session/authentication practices
- Avoid returning password hashes
- Sanitize or safely handle user-generated content
- Configure appropriate CORS rules if required


---


50. Backend Folder Structure


Recommended structure:


AquaWise/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── backend/
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── assessment.py
│   │   ├── usage.py
│   │   ├── recommendation.py
│   │   ├── ai.py
│   │   ├── achievement.py
│   │   └── streak.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── assessment.py
│   │   ├── dashboard.py