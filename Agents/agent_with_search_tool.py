import os
import logging
import asyncio
import vertexai

from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_and_search_tool.log"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)

print("✅ LOGGERS ARE CONFIGURED, LOADED AND READY TO GO!")




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info('Found project id!')
else:
    logger.error("No project id found. AI features will be disabled.")

session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")




from agents import create_day_trip_agent
from agent_query import run_agent_query

day_trip_agent= create_day_trip_agent()
print(f"AGENT: {day_trip_agent.name} IS UP AND READY TO CREATE TRIPS.")




#  <-----     IV.    FUNCTION TO TEST THE DAY TRIP AGENT    ----->

async def run_day_trip_genie() -> None:

    day_trip_session = await session_service.create_session(app_name=day_trip_agent.name, user_id=my_user_id)
    query = "Plan a relaxing and artsy day trip in Chicago, Il. Keep it affordable!"
    print(f"USER QUERY: '{query}'")
    await run_agent_query(day_trip_agent, query, day_trip_session, my_user_id, session_service)






if __name__ == "__main__":
    asyncio.run(run_day_trip_genie())






"""
✅ FINAL RESPONSE:
Here's a relaxing and artsy day trip itinerary for you in Chicago, focusing on affordable options for Friday, April 18, 2026:

**Morning (9:30 AM - 12:00 PM): Botanical Beauty and Public Art**

Start your day with a serene visit to the **Lincoln Park Conservatory**. 
This historic Victorian glass house offers a tropical escape with lush plant collections, and admission is free.
You'll be able to enjoy the "Jewels of Spring – Spring Flower Show" which is running until May 10, 2026.
Timed-entry tickets are required, so it's advisable to book these in advance. After exploring the Conservatory,
take a relaxing stroll through the surrounding **Lincoln Park**, enjoying the peaceful atmosphere and beautiful views.

**Lunch (12:30 PM - 1:30 PM): Affordable Bites in an Artsy Neighborhood**

Head to the vibrant **Wicker Park** neighborhood, known for its artistic flair and diverse, affordable dining scene.
For a budget-friendly and delicious lunch, consider **Sultan's Market**, a long-running Middle Eastern spot famous for its inexpensive falafel and shawarma wraps.
Alternatively, **Handlebar** offers a menu with vegetarian and pescatarian options in a casual setting.

**Afternoon (1:30 PM - 5:00 PM): Wicker Park's Creative Pulse**

After lunch, immerse yourself in Wicker Park's artsy environment.
Explore the **Flatiron Arts Building**, home to numerous artist studios and galleries across its three floors.
While the "First Friday" art walk isn't on this specific date, many studios might still be open for viewing, and the building itself is a hub of creativity.
Wander through the neighborhood streets, discovering colorful murals, unique boutiques, and a lively, bohemian atmosphere.
This is a great opportunity to relax and soak in local Chicago culture.

**Evening (6:00 PM - 9:00 PM): Free Culture and Relaxed Dining**

For your evening activity, engage with Chicago's cultural offerings:

*   **Chicago Humanities Festival:** The **Chicago Humanities Festival** begins on April 18, 2026, offering a range of "thought-provoking discussions and performances."
    Check their specific schedule for the day, as many events may be free or low-cost, aligning perfectly with both your artsy and affordable preferences.
*   **Civic String Quartet Concert:** Alternatively, members of the **Civic Orchestra of Chicago**
    perform free chamber concerts at various community venues throughout the city from April 18 to May 16, 2026.
    Check for specific performance times and locations on April 18 to enjoy some classical music in a relaxed setting.

After your cultural experience, enjoy a relaxed and affordable dinner back in Wicker Park or a nearby neighborhood.
Many of the lunch spots offer dinner options, or you can explore other casual eateries in the area.
"""