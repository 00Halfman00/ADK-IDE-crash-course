import os
import asyncio
import logging
import vertexai

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService



print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_with_memory_adaptive_planner.log"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)

print("✅ LOGGERS ARE CONFIGURED, LOADED AND READY TO GO!")




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", 'us-central1')

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    logger.error("No project id found. AI features will be disabled.")

session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")



# <-----  III.   DEFINE THE ADAPTIVE PLANNER WITH MEMORY AGENT  ------>

from agents import create_multi_day_trip_agent
from agent_query import run_agent_query

multi_day_trip_agent = create_multi_day_trip_agent()
print("✅ ADAPTIVE AGENT IS LOADED AND READY TO GO!")



#  <-----     IV.    FUNCTION TO TEST ADAPTATION AND MEMORY    ----->

async def test_adaptive_memory_demonstration() -> None:
    print("AGENT THAT ADAPTS THE SAME SESSION.")

    # Create a session that will be reused for the entire conversation
    trip_session = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    print(f"CREATED SESSION FOR TRIP: {trip_session.id}")

    # Turn 1: The user initiates the trip
    query1 = "Hi! I want to plan a 2-day trip to Rome, Italy. I'm into historic sites and great local food."
    print(F"\nUSER (TURN 1): '{query1}'")
    await run_agent_query(multi_day_trip_agent, query1, trip_session, my_user_id, session_service)

    # Turn 2: The user gives feedback and ask for a change
    # The same trip session object is used to enable continuous memory
    query2 = "That sounds good, but I am not a huge fan of violence. Can you replace the activity for Day 1 with something else historical?"
    print(f"\nUSER (TURN 2) FEEDBACK: '{query2}'")
    await run_agent_query(multi_day_trip_agent, query2, trip_session, my_user_id, session_service)

    # Turn 3: The user confirms and asks to continue
    query3 = "Yes, the new plan for Day 1 is perfect! Please plan Day 2 now, keeping the food theme in mind."
    print(f"\nUSER (TURN 3) CONFIRMATION: '{query3}'")
    await run_agent_query(multi_day_trip_agent, query3, trip_session, my_user_id, session_service)
 


if __name__ == "__main__":
    asyncio.run(test_adaptive_memory_demonstration())




"""
USER (TURN 1): 'Hi! I want to plan a 2-day trip to Rome, Italy. I'm into historic sites and great local food.'

--------------------------------------------------
✅ FINAL RESPONSE:
Hello! A 2-day trip to Rome focusing on historic sites and great local food sounds fantastic!

Let's start by planning **Day 1**. How about this:

**Day 1: Ancient Wonders and Roman Delights**

*   **Morning (9:00 AM - 1:00 PM): Colosseum and Roman Forum Exploration**
    Begin your day by immersing yourself in ancient Roman history. Explore the iconic Colosseum, the largest amphitheater ever built, and then wander through the ruins of the Roman Forum and Palatine Hill, once the center of Roman public life.
*   **Lunch (1:00 PM - 2:30 PM): Trastevere Trattoria Experience**
    Head over to the charming Trastevere neighborhood for lunch. Find a traditional trattoria and savor authentic Roman pasta dishes like Cacio e Pepe or Carbonara, along with some local wine.
*   **Afternoon (2:30 PM - 6:00 PM): Pantheon and Piazza Navona**
    After lunch, cross the Tiber and visit the magnificent Pantheon, a remarkably preserved ancient Roman temple. Afterwards, take a leisurely stroll to Piazza Navona, admire its beautiful fountains, and soak in the vibrant atmosphere.
*   **Evening (7:00 PM onwards): Roman Food Tour in Testaccio**
    For dinner, I suggest a guided food tour in the Testaccio district, known as Rome's culinary heart. You'll get to taste a variety of local specialties, from street food to traditional dishes, and learn about the city's gastronomic culture.

How does this sound for your first day in Rome?


USER (TURN 2) FEEDBACK: 'That sounds good, but I am not a huge fan of violence. Can you replace the activity for Day 1 with something else historical?'


✅ FINAL RESPONSE:
Understood! I appreciate your feedback. The Colosseum, while historically significant, does have a past tied to gladiatorial contests.

Let's revise **Day 1** to focus on other equally rich historical and cultural experiences in Rome:

**Day 1: Vatican City and Roman Delights**

*   **Morning (9:00 AM - 1:00 PM): Vatican City Exploration**
    Begin your day with a deep dive into Vatican City, the world's smallest independent state. Explore St. Peter's Basilica, a masterpiece of Renaissance architecture, and then visit the Vatican Museums, home to an incredible collection of art and artifacts, culminating in the awe-inspiring Sistine Chapel.
*   **Lunch (1:00 PM - 2:30 PM): Trastevere Trattoria Experience**
    Head over to the charming Trastevere neighborhood for lunch. Find a traditional trattoria and savor authentic Roman pasta dishes like Cacio e Pepe or Carbonara, along with some local wine.
*   **Afternoon (2:30 PM - 6:00 PM): Pantheon and Piazza Navona**
    After lunch, cross the Tiber and visit the magnificent Pantheon, a remarkably preserved ancient Roman temple. Afterwards, take a leisurely stroll to Piazza Navona, admire its beautiful fountains, and soak in the vibrant atmosphere.
*   **Evening (7:00 PM onwards): Roman Food Tour in Testaccio**
    For dinner, I suggest a guided food tour in the Testaccio district, known as Rome's culinary heart. You'll get to taste a variety of local specialties, from street food to traditional dishes, and learn about the city's gastronomic culture.

How does this revised Day 1 sound to you? We've swapped the ancient Roman arena for the cultural and spiritual heart of the Catholic world, still maintaining a strong historical focus.
--------------------------------------------------


USER (TURN 3) CONFIRMATION: 'Yes, the new plan for Day 1 is perfect! Please plan Day 2 now, keeping the food theme in mind.'



✅ FINAL RESPONSE:
Great! I'm glad Day 1 is perfect. Let's move on to an exciting **Day 2**, keeping your love for historic sites and amazing local food in mind.

Here’s a plan for your second day in Rome:

**Day 2: Imperial Rome, Markets, and Culinary Creations**

*   **Morning (9:00 AM - 1:00 PM): Roman Forum and Palatine Hill**
    Begin your day by stepping back into the heart of ancient Rome. Explore the vast and atmospheric ruins of the Roman Forum, once the bustling center of political and social life. Afterwards, ascend Palatine Hill, one of the most ancient parts of the city, offering incredible panoramic views of the Forum and the Circus Maximus.
*   **Lunch (1:00 PM - 2:30 PM): Campo de' Fiori Market Experience**
    Head to the lively Campo de' Fiori, one of Rome's most famous market squares. Wander through the vibrant stalls, sampling local delicacies and fresh produce. You can enjoy a casual and authentic Italian lunch at one of the many eateries surrounding the piazza.
*   **Afternoon (2:30 PM - 6:00 PM): Castel Sant'Angelo and Tiber River Walk**
    Visit Castel Sant'Angelo, a magnificent cylindrical fortress with a rich history, originally built as Emperor Hadrian's mausoleum. Explore its various levels and enjoy the views from the top. Afterwards, take a leisurely stroll across the beautiful Ponte Sant'Angelo, admiring its angelic sculptures as you walk along the Tiber River.
*   **Evening (7:00 PM onwards): Hands-on Roman Cooking Class**
    To truly immerse yourself in Rome's food culture, I suggest a hands-on Roman cooking class. Learn to prepare classic dishes like fresh pasta (e.g., fettuccine or ravioli), a traditional Roman main course, and perhaps a delightful tiramisu. You'll then enjoy the delicious meal you've prepared, complete with local wine.

How does this sound for your second day in Rome?
"""