AQUAWISE


Water Conservation Recommendation System


Project Type: Environmental Studies / CA Group Project
Project Category: Web-based Water Conservation & Recommendation System
Target Users: General public, household users, and especially farmers
Team Size: 3 members
Document Purpose: This document is the single source of truth for developing the AquaWise application. An AI development agent should use these requirements when designing, coding, testing, and modifying the project.


---


1. PROJECT OVERVIEW


AquaWise is a web-based water conservation recommendation system that helps users understand their estimated water consumption and discover practical ways to reduce unnecessary water usage.


The system collects information about a user's water-use habits, estimates their average daily water consumption, identifies areas with relatively high consumption, and generates personalized water-conservation recommendations.


AquaWise should support both:


1. Household users
2. Farmers / agricultural users


The system should maintain the user's historical records so that they can compare their water consumption over different weeks or months.


The application should have a visually appealing, modern, environmentally themed interface and should use charts, cards, progress indicators, and other visual elements to make the information easy to understand.


---


2. PROBLEM STATEMENT


Water is a limited natural resource, but users often do not know how much water they consume or which activities contribute most to their consumption.


Many people receive generic water-saving advice, but generic advice may not address their individual habits.


Farmers also have different water requirements from household users because agricultural activities such as irrigation can account for a significant portion of their water usage.


AquaWise aims to solve this problem by providing:


- Estimated daily water consumption
- Activity-wise consumption breakdown
- Identification of major water-use areas
- Personalized conservation recommendations
- Historical consumption tracking
- Visual analytics
- AI-powered assistance


---


3. PROJECT OBJECTIVES


The main objectives of AquaWise are:


1. Estimate a user's average daily water consumption.
2. Help users understand where their water is being used.
3. Identify potentially high-consumption activities.
4. Provide personalized water conservation recommendations.
5. Allow users to save and view historical consumption data.
6. Allow weekly and monthly comparison.
7. Provide visual charts and dashboards.
8. Provide an AI assistant for water-conservation questions.
9. Encourage users to adopt practical water-saving habits.
10. Provide additional support for agricultural users and farmers.


---


4. TARGET USERS


4.1 Household Users


Examples:


- Students
- Families
- Individual users
- Urban households
- Rural households


Household users should be able to provide information about activities such as:


- Household size
- Bathing/showering
- Toilet usage
- Tap usage
- Laundry
- Kitchen usage
- Dishwashing
- Vehicle washing
- Gardening
- Other household water usage


---


4.2 Farmers / Agricultural Users


Farmers should have a separate agricultural usage section rather than being forced to answer only household questions.


Relevant agricultural inputs may include:


- Farm area
- Crop type
- Number of irrigation events
- Irrigation duration
- Irrigation method
- Estimated water used for irrigation
- Frequency of irrigation
- Rainfall/rainwater availability
- Water source
- Other agricultural water usage


Possible irrigation methods:


- Flood irrigation
- Drip irrigation
- Sprinkler irrigation
- Other


The system should use these inputs to provide agriculture-specific recommendations.


---


5. USER FLOW


The basic user journey should be:


Landing Page
↓
Select User Type
↓
Household / Farmer
↓
Enter Water Usage Information
↓
Validate Inputs
↓
Estimate Water Consumption
↓
Analyze Usage
↓
Generate Personalized Recommendations
↓
Display Dashboard
↓
Save Result
↓
View Historical Data
↓
Compare Weekly/Monthly Usage
↓
Ask AquaWise AI Assistant if needed


---


6. CORE FEATURES


6.1 User Type Selection


When beginning an assessment, the user should select:


- Household
- Farmer / Agriculture


The questionnaire should dynamically change according to the selected category.


---


7. HOUSEHOLD INPUTS


The household questionnaire should use a combination of numerical inputs, dropdowns, radio buttons, and selectable options.


The following information should be collected.


7.1 Basic Information


- Number of people in household
- Assessment date


7.2 Bathing / Shower Usage


- Number of showers/baths per day
- Average duration per shower/bath
- Optional bathing method:
  - Shower
  - Bucket
  - Other


7.3 Toilet Usage


- Approximate number of toilet flushes per day
- Toilet type if the user knows it


7.4 Laundry


- Number of laundry loads per week
- Approximate washing machine capacity or water-use category


The user should not be required to know exact litres.


7.5 Kitchen / Dishwashing


- Number of people using the kitchen
- Approximate dishwashing frequency
- Method:
  - Running tap
  - Filled sink/basin
  - Dishwasher
  - Other


7.6 Vehicle Washing


- Number of vehicles
- Vehicle washing frequency
- Washing method:
  - Hose
  - Bucket
  - Pressure washer
  - Other


7.7 Gardening


- Whether the user maintains a garden
- Approximate gardening frequency
- Approximate watering duration
- Watering method:
  - Hose
  - Bucket
  - Sprinkler
  - Drip
  - Other


7.8 Other Water Usage


Allow the user to enter additional information where relevant.


Examples:


- Cleaning
- House washing
- Pets
- Other activities


The system should not force users to provide information that does not apply to them.


---


8. FARMER / AGRICULTURAL INPUTS


For agricultural users, the system should collect:


Basic Information


- Farm area
- Crop type
- Location/region (optional)
- Assessment date


Irrigation


- Irrigation frequency
- Average irrigation duration
- Irrigation method
- Estimated water used per irrigation, if known


Water Source


Possible options:


- Groundwater
- Canal
- Rainwater
- Reservoir
- Other


Crop Information


Allow users to select common crop categories and provide a custom option.


Example categories:


- Wheat
- Rice
- Maize
- Vegetables
- Pulses
- Fruits
- Other


The system should avoid pretending to provide professional agronomic advice. Recommendations should be framed as general water-conservation suggestions.


---


9. WATER CONSUMPTION CALCULATION


The system should calculate an estimated average daily water consumption.


The result should clearly state that it is an estimate rather than an exact measurement.


Example:


«Estimated Daily Water Consumption
385 L/day»


The calculation system should use configurable water-use assumptions rather than hard-coding unexplained numbers throughout the application.


For example:


Shower consumption =
number of showers × average duration × estimated flow rate


Similarly:


Laundry daily equivalent =
weekly laundry water usage ÷ 7


and:


Vehicle washing daily equivalent =
water used per wash × washes per week ÷ 7


The system should convert weekly activities into daily equivalents where appropriate.


---


10. CONFIGURABLE WATER-USAGE ASSUMPTIONS


All estimated water-use values should be stored centrally.


Example configuration:


SHOWER_FLOW_RATE
TOILET_FLUSH_VOLUME
LAUNDRY_WATER_PER_LOAD
DISHWASHING_WATER_RATE
VEHICLE_WASH_WATER
GARDENING_WATER_RATE


These values should be easy for the developers to modify later.


The interface should not falsely imply that these values are universally exact.


The application should use language such as:


«"Estimated based on typical usage assumptions."»


---


11. CONSUMPTION BREAKDOWN


After calculation, the system should show the user's estimated consumption by activity.


Example:


Activity| Estimated Usage
Bathing| 120 L
Toilet| 60 L
Laundry| 55 L
Kitchen| 70 L
Gardening| 40 L
Vehicle Washing| 20 L
Other| 20 L


The exact values will depend on the user's inputs.


The dashboard should visually represent this using charts.


Recommended charts:


- Doughnut/pie chart for activity breakdown
- Bar chart for weekly/monthly usage
- Line chart for historical trends


---


12. PERSONALIZED RECOMMENDATION SYSTEM


AquaWise must not simply display the same generic list of tips to every user.


Recommendations should be generated based on the user's input and consumption profile.


For example:


If shower usage is high:


«"Your bathing activity contributes significantly to your estimated water use. Consider reducing shower duration or using a lower-flow showerhead."»


If vehicle washing is frequent:


«"Your vehicle-washing frequency may be contributing to your water use. Consider using a bucket instead of continuously running a hose."»


If gardening usage is high:


«"Consider watering plants during cooler parts of the day and using drip irrigation where practical."»


For farmers:


«"Your selected irrigation method may allow opportunities to reduce water loss. Consider exploring drip or sprinkler irrigation where suitable for your crop and conditions."»


Recommendations should contain:


- Problem identified
- Reason
- Suggested action
- Estimated potential saving where it can reasonably be calculated


---


13. AI-POWERED RECOMMENDATIONS


AI may be used to improve personalization.


The AI should receive structured information such as:


User Type
Household Size
Estimated Daily Consumption
Activity Breakdown
High-Usage Activities
User Habits
Agricultural Information (if applicable)


The AI should then generate practical recommendations.


The AI must:


- Base recommendations on available user data.
- Avoid inventing user information.
- Avoid presenting estimates as exact measurements.
- Avoid giving dangerous or misleading instructions.
- Keep recommendations understandable to general users.
- Prioritize practical water-saving actions.


AI should complement the calculation engine rather than replace it.


The basic calculation system should still work if the AI service is unavailable.


---


14. AI ASSISTANT


AquaWise should include an optional AI assistant.


The assistant can answer questions such as:


«"How can I save water while doing laundry?"»


«"How much water can I save by reducing shower time?"»


«"What is drip irrigation?"»


«"How can I reduce water wastage on my farm?"»


The assistant should use AquaWise's context where appropriate.


For example, if a user has high gardening consumption, the assistant can provide gardening-specific suggestions.


The assistant should clearly distinguish between:


- Calculated AquaWise estimates
- General educational information
- AI-generated suggestions


---


15. DASHBOARD


The dashboard is a mandatory feature.


It should be visually appealing and easy to understand.


The main dashboard should contain:


Summary Cards


- Estimated Daily Usage
- Estimated Weekly Usage
- Estimated Monthly Usage
- Potential Water Saving


Usage Breakdown


Display consumption by activity.


Highest Usage Area


Example:


«Highest Usage Area
Bathing»


Conservation Score


A simple score can be calculated based on the user's estimated usage and conservation habits.


Example:


«💧 Water Saver Score: 72/100»


The score should be presented as a motivational indicator rather than a scientifically validated environmental score.


Recommendations


Show the most relevant recommendations.


Historical Trend


Display previous assessments.


---


16. WATER-SAVING SCORE


AquaWise may include a gamified Water Saver Score.


Example:


Water Saver Score
72 / 100


Possible levels:


- Getting Started
- Water Saver
- Smart Water User
- Water Champion


The score should be based on defined rules rather than arbitrary AI judgment.


Example factors:


- Estimated consumption
- Water-saving habits
- Frequency of wasteful activities
- Use of efficient irrigation methods
- Adoption of recommendations


The scoring system should be configurable.


---


17. HISTORY & DATA STORAGE


Users must be able to save their assessments.


Each assessment should contain:


- User ID
- Date
- User type
- Estimated daily consumption
- Estimated weekly consumption
- Estimated monthly consumption
- Activity breakdown
- Recommendations
- Water Saver Score


The system should allow users to view previous assessments.


---


18. WEEKLY & MONTHLY COMPARISON


Users should be able to compare their water usage over time.


Example:


Previous Month:
11,400 L


Current Month:
9,850 L


Change:
-1,550 L


The interface should clearly indicate whether consumption increased or decreased.


Charts should show trends over time.


The system should avoid claiming that a reduction is guaranteed to represent actual physical water savings unless the measurement is based on real meter data.


---


19. DATABASE


A database should be used to store user and assessment information.


A simple relational database such as SQLite is sufficient for the initial version.


Suggested tables:


Users


id
name
email
password_hash
user_type
created_at


Assessments


id
user_id
assessment_date
daily_consumption
weekly_consumption
monthly_consumption
water_score


Usage Details


id
assessment_id
activity
estimated_consumption


Recommendations


id
assessment_id
recommendation
category
potential_saving


AI Conversations


If AI chat history is implemented:


id
user_id
message
response
created_at


---


20. USER AUTHENTICATION


Users should be able to:


- Create an account
- Log in
- Log out
- Access their dashboard
- View previous assessments


Passwords must never be stored as plain text.


They should be securely hashed if authentication is implemented.


---


21. MAIN WEBSITE PAGES


The application should contain at least the following pages.


21.1 Home Page


Purpose:


Introduce AquaWise.


Sections:


- Hero section
- Short explanation
- "Calculate My Water Usage" button
- Key benefits
- How AquaWise works
- Call to action


---


21.2 Assessment Page


Allow the user to select:


- Household
- Farmer


Then display the appropriate questionnaire.


---


21.3 Results Page


Show:


- Estimated daily consumption
- Weekly/monthly estimate
- Usage breakdown
- High-consumption areas
- Personalized recommendations
- Water Saver Score


---


21.4 Dashboard


Show:


- Current statistics
- Charts
- Historical data
- Recommendations
- Comparison information


---


21.5 History Page


Show previous assessments.


Allow:


- Viewing previous results
- Weekly comparison
- Monthly comparison
- Trend visualization


---


21.6 AI Assistant Page / Widget


Provide a conversational interface for water-related questions.


---


21.7 Profile Page


Allow users to view/update:


- Name
- Email
- User type
- Other relevant preferences


---


22. USER INTERFACE REQUIREMENTS


The website should have a modern environmental theme.


Recommended visual direction:


- Blue/green environmental color palette
- Clean white/neutral backgrounds
- Rounded cards
- Clear typography
- Modern icons
- Subtle animations
- Responsive layout
- Charts and visual statistics
- Clear call-to-action buttons


The website should feel like a modern environmental technology platform rather than a basic college HTML project.


---


23. RESPONSIVENESS


The application must work on:


- Desktop
- Laptop
- Tablet
- Mobile


The layout should adapt automatically to different screen sizes.


Forms must remain usable on mobile devices.


Charts should resize appropriately.


---


24. FRONTEND TECHNOLOGY


Recommended initial stack:


HTML5
CSS3
JavaScript
Chart.js


A frontend framework such as React may be used only if the development team is comfortable with it.


For a beginner-friendly implementation, vanilla HTML/CSS/JavaScript is acceptable.


---


25. BACKEND TECHNOLOGY


Recommended:


Python
Flask


Responsibilities:


- Authentication
- Processing assessment data
- Calculating consumption
- Generating/storing recommendations
- Communicating with AI APIs
- Database operations
- Historical data retrieval


---


26. DATABASE TECHNOLOGY


Recommended:


SQLite


The project should be structured so that SQLite can later be replaced by PostgreSQL or another database if necessary.


---


27. AI INTEGRATION


AI integration should be modular.


Recommended architecture:


Frontend
    ↓
Flask Backend
    ↓
Calculation Engine
    ↓
Recommendation Engine
    ↓
AI Service (optional)
    ↓
Database


The application should continue to provide basic recommendations if the AI API is unavailable.


AI API keys must never be exposed in frontend JavaScript.


API keys should be stored using environment variables.


Example:


.env


The ".env" file must not be committed to GitHub.


---


28. RECOMMENDATION ENGINE


The system should first identify relevant categories using deterministic rules.


Example:


IF shower_consumption > threshold
    → bathing recommendation


IF gardening_consumption > threshold
    → gardening recommendation


IF vehicle_washing_frequency > threshold
    → vehicle recommendation


IF irrigation_method == "flood"
    → irrigation efficiency recommendation


AI can then personalize the language and combine relevant recommendations.


This hybrid approach is preferred over allowing an AI model to independently calculate everything.


---


29. VALIDATION


The system must validate user input.


Examples:


- Household size cannot be zero or negative.
- Shower duration cannot be negative.
- Number of showers cannot be negative.
- Farm area cannot be negative.
- Irrigation frequency cannot be negative.
- Required fields cannot be empty.
- Email must have valid format.
- Password requirements should be enforced.


The application should display clear error messages.


Example:


«"Please enter a valid household size."»


---


30. ERROR HANDLING


The application should gracefully handle:


- Invalid input
- Missing input
- Database errors
- Failed AI requests
- Network errors
- Authentication errors
- Server errors


The user should receive understandable messages instead of technical error traces.


---


31. SECURITY REQUIREMENTS


The application should:


- Never expose API keys in frontend code.
- Hash passwords.
- Validate user input.
- Use parameterized database queries.
- Prevent unauthorized access to another user's history.
- Keep authentication information secure.
- Avoid storing unnecessary personal information.


---


32. PRIVACY


AquaWise should collect only information necessary for the application's functionality.


Users should be informed that consumption figures are estimates.


The application should not claim to be an official water-metering system.


---


33. CALCULATION DISCLAIMER


The results page should include a small disclaimer:


«"AquaWise provides estimated water consumption based on the information you provide and typical usage assumptions. Actual consumption may vary."»


This is important because the system does not directly measure water flow.


---


34. FARMING DISCLAIMER


Agricultural recommendations should be general conservation suggestions.


The system should not present itself as a replacement for:


- Agricultural experts
- Irrigation engineers
- Local authorities
- Crop-specific professional advice


Recommendations involving crop water requirements should be presented cautiously because requirements vary by crop, climate, soil, irrigation method, and local conditions.


---


35. GAMIFICATION


Optional gamification features should include:


- Water Saver Score
- Achievement badges
- Conservation levels
- Progress indicators


Example badges:


💧 First Assessment
🌱 Water Saver
🚿 Smart Shower User
🌾 Smart Irrigator
♻️ Conservation Champion


Gamification should encourage engagement without making scientifically unsupported claims.


---


36. FUTURE FEATURES


The following features are NOT required for the first MVP but can be added later:


- IoT water meter integration
- Real-time water monitoring
- Smart-home integration
- Weather API integration
- Local rainfall data
- Crop-specific irrigation recommendations
- Regional water scarcity information
- Com