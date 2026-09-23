AquaWise — App Flow Document


1. Document Purpose


This document defines the complete user flow and application flow for AquaWise — Water Conservation Recommendation System.


It explains:


- How users navigate through the application
- What happens at each stage
- What information the user provides
- How the system processes the information
- How recommendations and results are displayed
- How users access their dashboard and history
- How the AI assistant fits into the application


This document should be used as a reference by the development team and AI coding/development agents.


---


2. Overall Application Flow


The main AquaWise flow is:


Landing Page → Register/Login → Select User Type → Water Usage Assessment → Consumption Calculation → Results → Personalized Recommendations → Dashboard → History / AI Assistant


A returning user can directly access:


Login → Dashboard → New Assessment / History / AI Assistant / Profile


---


3. Application Entry Flow


3.1 Landing Page


When a user opens AquaWise, they see the landing page.


Main elements


- AquaWise logo/name
- Short description of the application
- "Calculate My Water Usage" button
- "Login" button
- "Sign Up" button
- Brief explanation of how AquaWise works
- Visual representation of water conservation


Primary action


The main CTA should be:


Calculate My Water Usage


If the user is not logged in, clicking it should lead to:


Login / Register → Assessment


---


4. Authentication Flow


4.1 New User


Flow:


Landing Page → Sign Up → Registration Form → Account Created → User Type Selection → Assessment


Registration fields


- Name
- Email
- Password
- Confirm Password


After successful registration:


Account Created → User Type Selection


---


4.2 Existing User


Flow:


Landing Page → Login → Email + Password → Dashboard


The user can then choose:


- New Assessment
- View Dashboard
- View History
- AI Assistant
- Profile


---


4.3 Authentication Error Flow


If login fails:


Login → Invalid Credentials → Error Message → Try Again


The system should not reveal sensitive authentication information.


---


5. User Type Selection


After registration, the user selects their primary usage category.


Options


1. Household User


For people who mainly use water at home.


2. Farmer / Agricultural User


For users who mainly use water for farming or irrigation.


The selected user type determines which assessment form is displayed.


---


6. Household Assessment Flow


6.1 Household Information


The user provides basic information.


Inputs


- Household size
- Number of people regularly using water
- Location (optional)
- Number of bathrooms
- Other relevant household information


After clicking Next:


Household Information → Daily Activities


---


7. Household Daily Water Usage


The user provides information about their common water-consuming activities.


Shower / Bath


Inputs may include:


- Showers/baths per day
- Average duration
- Type of bathing


Toilet Usage


Inputs may include:


- Number of toilet uses per person/day
- Toilet type, if required


Laundry


Inputs may include:


- Laundry loads per week
- Approximate load size


Kitchen / Dishwashing


Inputs may include:


- Dishwashing frequency
- Approximate duration
- Kitchen water usage


Vehicle Washing


Inputs:


- Vehicle washing frequency
- Approximate method of washing


Gardening


Inputs:


- Gardening frequency
- Approximate duration
- Garden size, if applicable


Other Usage


Optional field for additional water usage.


---


8. Farmer / Agricultural Assessment Flow


If the user selects Farmer / Agricultural User, the household form is replaced by the agricultural assessment.


8.1 Farm Information


Inputs:


- Farm area
- Crop type
- Number of crops
- Water source


Possible water sources:


- Groundwater
- Canal
- Rainwater
- Tank
- Other


---


8.2 Irrigation Information


Inputs:


- Irrigation method
- Irrigation frequency
- Irrigation duration
- Approximate water quantity, if known
- Number of irrigation sessions


Possible irrigation methods:


- Flood irrigation
- Drip irrigation
- Sprinkler irrigation
- Other


---


8.3 Rainfall / Rainwater Information


Optional inputs:


- Recent rainfall
- Rainwater harvesting availability
- Use of stored rainwater


After submission:


Farm Information → Irrigation Information → Calculation


---


9. Assessment Validation Flow


Before calculation, the application validates the submitted information.


Validation checks


- Required fields are completed
- Numerical values are valid
- Values are within reasonable ranges
- Negative values are rejected
- Invalid text/numeric combinations are rejected


If validation fails:


Assessment → Validation Error → Highlight Incorrect Field → User Corrects Input


If validation succeeds:


Assessment → Calculation Engine


---


10. Water Consumption Calculation Flow


The backend receives the assessment data.


Flow:


User Input → Backend API → Validation → Calculation Engine → Consumption Estimate


The calculation engine estimates:


- Daily water consumption
- Weekly water consumption
- Monthly water consumption


The system should calculate different categories separately where possible.


Example:


Daily Consumption = Shower + Toilet + Laundry + Kitchen + Vehicle + Gardening + Other


The exact calculation assumptions should be stored in the backend so they can be modified without changing the frontend.


---


11. Consumption Breakdown


After calculation, AquaWise generates a breakdown of estimated consumption.


Example categories:


- Bathroom
- Kitchen
- Laundry
- Vehicle washing
- Gardening
- Other


For agricultural users:


- Irrigation
- Crop usage
- Other agricultural activities


The application converts the calculated values into understandable visual information.


---


12. Results Page


After calculation, the user reaches the Results page.


12.1 Main Results


The page should display:


Estimated Daily Consumption


Example:


Estimated Water Usage: 420 L/day


Weekly Estimate


2,940 L/week


Monthly Estimate


12,600 L/month


The numbers should be clearly visible.


---


13. Consumption Visualization


The Results page should contain charts.


Possible charts:


Pie / Doughnut Chart


Shows the percentage of water used by each category.


Bar Chart


Compares water consumption between categories.


Example:


Bathroom █████████
Kitchen █████
Laundry ████
Gardening ███


Charts should be generated using Chart.js.


---


14. Water Conservation Score


AquaWise calculates a simple Water Saver Score based on the user's estimated usage and conservation opportunities.


Example:


Water Saver Score: 72/100


The score is intended to give users an understandable summary of their current conservation situation.


The calculation should be deterministic and handled by the backend.


---


15. Recommendation Flow


After calculating consumption:


Consumption Data → Recommendation Engine → Personalized Recommendations


The recommendation engine examines areas where the user has significant water usage or potential savings.


Examples:


- Reduce shower duration
- Improve laundry practices
- Avoid unnecessary running water
- Use efficient vehicle-washing methods
- Improve irrigation efficiency
- Consider drip irrigation
- Use rainwater harvesting where appropriate


Recommendations should be connected to the user's submitted data rather than being completely generic.


---


16. AI Recommendation Flow


AquaWise can optionally use an AI service to personalize recommendations.


Flow:


User Data → Calculation Engine → Rule-Based Recommendations → AI Service → Personalized Explanation


The AI should not be responsible for calculating the core water-consumption numbers.


The preferred architecture is:


Deterministic Calculation → AI Personalization


This ensures that numerical calculations remain consistent while AI can improve the explanation and personalization.


If the AI service is unavailable:


AI Unavailable → Rule-Based Recommendations → Display Recommendations


The application should continue functioning.


---


17. Recommendations Page


The Recommendations section should display cards.


Each card can contain:


- Recommendation title
- Explanation
- Relevant usage category
- Suggested action
- Potential conservation benefit, where reliably estimable


Example:


Reduce Shower Duration


Your shower usage represents a significant portion of your estimated household water consumption.


Suggested Action: Try reducing unnecessary shower time.


---


18. Dashboard Flow


After completing an assessment, the user can access the dashboard.


Flow:


Results → Dashboard


The dashboard should provide a quick overview.


Dashboard Components


1. Current daily consumption
2. Weekly consumption
3. Monthly consumption
4. Water Saver Score
5. Highest-usage category
6. Top recommendations
7. Recent assessments
8. Consumption charts


---


19. Dashboard Navigation


The main navigation should contain:


Home | Assessment | Dashboard | History | AI Assistant | Profile


The navigation should remain consistent throughout the application.


---


20. History Flow


Users can view previous assessments.


Flow:


Dashboard → History


The History page displays previous records.


Each record can contain:


- Assessment date
- User type
- Daily consumption
- Weekly consumption
- Monthly consumption
- Water Saver Score


Users should be able to open an individual record for more details.


---


21. Comparison Flow


AquaWise should allow users to compare their water usage over time.


Example:


Previous Month → Current Month


The application can display:


- Previous consumption
- Current consumption
- Difference
- Percentage change


Example:


Previous Month: 14,000 L
Current Month: 12,600 L


Change: 1,400 L


The comparison should be presented neutrally as a change in recorded/estimated usage.


---


22. AI Assistant Flow


The AI Assistant can be accessed from the main navigation.


Flow:


Dashboard → AI Assistant → Ask Question → Backend → AI Service → Response


Users may ask questions such as:


- "How can I reduce my household water usage?"
- "Why is my gardening usage high?"
- "What are some ways to save water during summer?"
- "How can drip irrigation help?"


The AI assistant should use relevant user assessment information when available.


---


23. AI Assistant Fallback


If the external AI service is unavailable:


User Question → AI Service Failure → Fallback Message / Rule-Based Information


The rest of the application should remain functional.


---


24. Profile Flow


Flow:


Navigation → Profile


The user can view or edit basic account information.


Possible options:


- Name
- Email
- User type
- Account settings
- Logout


---


25. Logout Flow


Flow:


Profile → Logout → Session Ended → Landing/Login Page


After logout, protected pages should not remain accessible through an active session.


---


26. Complete New User Flow


The complete journey for a new household user is:


Landing Page
↓
Sign Up
↓
Create Account
↓
Select Household
↓
Household Information
↓
Daily Water Activities
↓
Submit Assessment
↓
Validation
↓
Water Consumption Calculation
↓
Consumption Breakdown
↓
Water Saver Score
↓
Personalized Recommendations
↓
Dashboard
↓
Save Assessment
↓
History


---


27. Complete Farmer Flow


The complete journey for a farmer is:


Landing Page
↓
Sign Up / Login
↓
Select Farmer / Agricultural User
↓
Farm Information
↓
Crop Information
↓
Irrigation Information
↓
Water Source / Rainfall Information
↓
Submit Assessment
↓
Validation
↓
Agricultural Water Consumption Calculation
↓
Consumption Breakdown
↓
Water Saver Score
↓
Recommendations
↓
Dashboard
↓
History


---


28. Returning User Flow


A returning user does not need to repeat registration.


Landing Page
↓
Login
↓
Dashboard
↓
Choose:


- New Assessment
- View Results
- View History
- Compare Usage
- Ask AI Assistant
- View Profile


---


29. Error Handling Flow


The application should handle common errors.


Invalid Input


Input → Validation Error → User Corrects Input


Server Error


Request → Server Error → Friendly Error Message → Retry


Database Error


Database Request → Failure → Error Logged → User-Friendly Message


AI API Error


AI Request → Failure → Fallback Recommendations / Message


Network Error


Request → Network Failure → Retry Option


Errors should not expose technical details such as database queries, API keys, or server configuration.


---


30. Data Flow


The basic data flow is:


User
↓
Frontend Form
↓
Flask API
↓
Input Validation
↓
Calculation Service
↓
Recommendation Service
↓
AI Service (Optional)
↓
Database
↓
Results
↓
Dashboard


---


31. Core Application Logic


AquaWise should follow this principle:


1. Collect


Collect water-usage information from the user.


2. Validate


Check whether the submitted information is valid.


3. Calculate


Estimate water consumption using deterministic formulas.


4. Analyze


Identify major water-consuming activities.


5. Recommend


Generate personalized conservation recommendations.


6. Personalize


Use AI where appropriate to improve explanations and suggestions.


7. Store


Save assessment results for future comparison.


8. Visualize


Present results through dashboards and charts.


---


32. Page-to-Page Flow


Page| Main Action| Next Page
Landing| Start / Login / Sign Up| Login/Register
Register| Create account| User Type
Login| Authenticate| Dashboard
User Type| Select user category| Assessment
Assessment| Enter water usage| Results
Results| View consumption| Recommendations/Dashboard
Recommendations| View suggestions| Dashboard
Dashboard| View overview| History/Assessment/AI
History| View previous records| Detailed Result
AI Assistant| Ask questions| AI Response
Profile| Manage account| Dashboard
Logout| End session| Login/Landing


---


33. Group Development Flow


Since AquaWise is a three-member group project, development should happen in parallel.


Member 1 — Frontend


Responsible for:


- Landing page
- Assessment forms
- Results page
- Dashboard UI
- History UI
- AI Assistant UI
- CSS/responsive design
- Chart.js integration


Member 2 — Backend & Database


Responsible for:


- Flask application
- API endpoints
- Database
- Authentication
- Data validation
- Consumption calculation
- Saving assessment history


Member 3 — AI & Recommendation System


Responsible for:


- Rule-based recommendation engine
- AI service integration
- AI prompts
- AI Assistant
- Personalized recommendation logic
- Water Saver Score logic


All three members should use Git/GitHub and coordinate changes through the shared repository.


---


34. MVP Flow


The first working version should focus on:


Register/Login
↓
Select User Type
↓
Assessment
↓
Water Consumption Calculation
↓
Results
↓
Recommendations
↓
Dashboard
↓
History


After this works, the team can add:


- AI Assistant
- Advanced AI personalization
- Gamification
- More detailed comparisons
- Additional visualizations


---


35. Final User Journey


The ideal AquaWise experience is:


«Enter → Assess → Calculate → Understand → Improve → Track»


The application should make the process simple enough for a beginner user while still providing meaningful technical functionality for the project evaluation.


The core principle of the application flow is:


User provides data → AquaWise calculates usage → AquaWise explains the results → AquaWise recommends actions → User tracks progress over time.