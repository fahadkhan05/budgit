"""
Recommendation Engine
======================
This module contains the core business logic for generating personalized
recommendations. It's intentionally kept in its own file, separate from
views.py.

LEARNING — Separation of Concerns:
  Business logic (what to recommend) should live separately from
  request handling (parsing HTTP requests and returning responses).
  This makes the engine easy to test and change without touching the views.

HOW IT WORKS:
  1. We define a database of recommendations, organized by:
       Interest Category → Budget Tier → List of suggestions

  2. Based on the user's remaining budget, we pick a "tier":
       Tier 1: < $25   (small/free activities)
       Tier 2: $25–75  (mid-range activities)
       Tier 3: $75–200 (bigger experiences)
       Tier 4: > $200  (splurge items)

  3. For each of the user's interests, we grab recommendations from
     the appropriate tier and return them all.

REAL-WORLD EQUIVALENT:
  In production you might replace this with an API call to an AI service,
  a database of curated content, or a machine learning recommendation model.
  The view code stays the same — you'd just swap out this engine module.
"""


# ---------------------------------------------------------------------------
# The Recommendation Database
# ---------------------------------------------------------------------------
# Structure: { interest_key: { tier: [ { title, description, cost, tags } ] } }
RECOMMENDATIONS = {
    'dining': {
        'tier1': [
            {
                'title': 'Explore a Food Truck',
                'description': "Find your city's food trucks on social media. Most meals run $8–15 and the variety is great.",
                'estimated_cost': '$8 – $15',
                'tags': ['food', 'local', 'casual'],
            },
            {
                'title': 'Cook a New Recipe',
                'description': "Pick an ambitious recipe you've never tried. Cooking builds a real skill AND saves money vs going out.",
                'estimated_cost': '$10 – $20',
                'tags': ['food', 'skill-building', 'home'],
            },
        ],
        'tier2': [
            {
                'title': 'Try a Highly-Rated Local Restaurant',
                'description': "Check Google Maps or Yelp for a spot you've been meaning to visit. Support local business!",
                'estimated_cost': '$25 – $60',
                'tags': ['food', 'experience', 'social'],
            },
            {
                'title': 'Weekend Brunch',
                'description': 'Brunch is the perfect social meal. Find a spot with good reviews and invite a friend.',
                'estimated_cost': '$20 – $40',
                'tags': ['food', 'social', 'weekend'],
            },
        ],
        'tier3': [
            {
                'title': 'Take a Cooking Class',
                'description': 'Learn a cuisine you love from a professional chef. Check local culinary schools or community centers.',
                'estimated_cost': '$75 – $150',
                'tags': ['food', 'skill-building', 'experience'],
            },
            {
                'title': 'Nice Dinner Out',
                'description': 'Treat yourself or a friend to a quality dining experience at a restaurant you normally save for special occasions.',
                'estimated_cost': '$80 – $150',
                'tags': ['food', 'experience', 'special'],
            },
        ],
        'tier4': [
            {
                'title': 'Book a Food Tour',
                'description': "A guided food tour takes you to 8–12 spots in one evening. Great for discovering hidden gems in your city.",
                'estimated_cost': '$80 – $120 per person',
                'tags': ['food', 'experience', 'guided'],
            },
        ],
    },

    'fitness': {
        'tier1': [
            {
                'title': 'Free Outdoor Workout',
                'description': 'Park workout, trail run, or bodyweight circuit. Search YouTube for "outdoor fitness routine" for ideas.',
                'estimated_cost': '$0',
                'tags': ['fitness', 'outdoor', 'free'],
            },
            {
                'title': '30-Day YouTube Fitness Challenge',
                'description': "Channels like Yoga with Adriene or Athlean-X have free 30-day programs. Pick one and commit.",
                'estimated_cost': '$0',
                'tags': ['fitness', 'home', 'free', 'commitment'],
            },
        ],
        'tier2': [
            {
                'title': 'Try a New Fitness Class',
                'description': "Most studios offer a discounted or free first class. Try yoga, pilates, kickboxing, or spin — find what you love.",
                'estimated_cost': '$15 – $30',
                'tags': ['fitness', 'social', 'try-new'],
            },
            {
                'title': 'Bike Rental Day',
                'description': 'Rent a bike and explore a trail or your city. Great cardio + sightseeing combo.',
                'estimated_cost': '$20 – $50',
                'tags': ['fitness', 'outdoor', 'exploration'],
            },
        ],
        'tier3': [
            {
                'title': 'Monthly Gym Membership',
                'description': "Commit to a gym for one month. If you go 3x/week, it's extremely cost-effective. Many gyms offer no-commitment month-to-month.",
                'estimated_cost': '$30 – $80/month',
                'tags': ['fitness', 'commitment', 'value'],
            },
            {
                'title': '2–3 Personal Training Sessions',
                'description': 'Book a trainer to build a program and learn proper form. An investment that pays off for years.',
                'estimated_cost': '$60 – $150',
                'tags': ['fitness', 'skill-building', 'investment'],
            },
        ],
        'tier4': [
            {
                'title': 'Quality Home Fitness Equipment',
                'description': "Invest in adjustable dumbbells, a pull-up bar, or resistance band set. One-time purchase, years of use.",
                'estimated_cost': '$150 – $400',
                'tags': ['fitness', 'investment', 'home'],
            },
        ],
    },

    'entertainment': {
        'tier1': [
            {
                'title': 'Movie Night at Home',
                'description': "Rent a new release ($4–6) or explore your streaming library. Upgrade it with homemade popcorn and good snacks.",
                'estimated_cost': '$5 – $15',
                'tags': ['entertainment', 'home', 'relaxation'],
            },
            {
                'title': 'Find a Free Local Event',
                'description': 'Check Eventbrite, Facebook Events, or your city\'s website for free concerts, markets, or festivals this weekend.',
                'estimated_cost': '$0 – $10',
                'tags': ['entertainment', 'local', 'social'],
            },
        ],
        'tier2': [
            {
                'title': 'Escape Room with Friends',
                'description': 'Book an escape room for 2–6 people. Collaborative, challenging, and more fun than most activities.',
                'estimated_cost': '$25 – $35 per person',
                'tags': ['entertainment', 'social', 'experience'],
            },
            {
                'title': 'Movie Theater Outing',
                'description': 'Some movies just need the big screen experience. Go for the full treatment — good seats, good snacks.',
                'estimated_cost': '$20 – $40',
                'tags': ['entertainment', 'social', 'casual'],
            },
        ],
        'tier3': [
            {
                'title': 'Live Concert or Comedy Show',
                'description': 'Buy tickets to see a local band, touring artist, or stand-up comedian. Check Bandsintown or Ticketmaster.',
                'estimated_cost': '$40 – $120',
                'tags': ['entertainment', 'live', 'experience'],
            },
            {
                'title': 'Minor League Sporting Event',
                'description': "Minor league games are affordable, fun, and often include between-inning entertainment. Much better experience than the price suggests.",
                'estimated_cost': '$15 – $40',
                'tags': ['entertainment', 'social', 'sports'],
            },
        ],
        'tier4': [
            {
                'title': 'Major Concert or Music Festival',
                'description': 'Splurge on tickets to a big artist or day pass to a festival. These create lasting memories.',
                'estimated_cost': '$100 – $300+',
                'tags': ['entertainment', 'experience', 'special'],
            },
        ],
    },

    'travel': {
        'tier1': [
            {
                'title': 'Explore a Nearby Town',
                'description': 'Drive 30–60 minutes and spend the day somewhere new. Historic districts, state parks, and small-town markets are usually free to explore.',
                'estimated_cost': '$10 – $25 (gas + coffee)',
                'tags': ['travel', 'local', 'exploration'],
            },
        ],
        'tier2': [
            {
                'title': 'Day Trip to a State Park',
                'description': "Pack a lunch, grab your water bottle, and spend a full day at a nearby state or national park. America's park system is world-class.",
                'estimated_cost': '$10 – $35',
                'tags': ['travel', 'outdoor', 'nature'],
            },
            {
                'title': 'Weekend Camping Trip',
                'description': 'Book a campsite 1–2 nights at a state park. Disconnecting from screens and sleeping under stars is genuinely restorative.',
                'estimated_cost': '$30 – $70 for the site',
                'tags': ['travel', 'outdoor', 'adventure'],
            },
        ],
        'tier3': [
            {
                'title': 'Overnight Road Trip',
                'description': "Pick a destination 2–4 hours away, book a budget motel or Airbnb. The drive itself is half the experience.",
                'estimated_cost': '$100 – $200',
                'tags': ['travel', 'adventure', 'experience'],
            },
        ],
        'tier4': [
            {
                'title': 'Long Weekend City Getaway',
                'description': 'Book a budget flight + Airbnb to a city on your list. 3-day weekends are enough to genuinely experience a new place.',
                'estimated_cost': '$200 – $500',
                'tags': ['travel', 'adventure', 'experience'],
            },
        ],
    },

    'shopping': {
        'tier1': [
            {
                'title': 'Thrift Store Treasure Hunt',
                'description': "Visit a Goodwill, Salvation Army, or local consignment shop. Great finds for almost nothing, and it's sustainable.",
                'estimated_cost': '$5 – $20',
                'tags': ['shopping', 'sustainable', 'discovery'],
            },
        ],
        'tier2': [
            {
                'title': 'Upgrade One Daily-Use Item',
                'description': "Replace something you use every day — water bottle, notebook, backpack — with a quality version. Small upgrade, big daily difference.",
                'estimated_cost': '$25 – $60',
                'tags': ['shopping', 'quality', 'daily-use'],
            },
        ],
        'tier3': [
            {
                'title': 'Invest in a Quality Clothing Piece',
                'description': "Buy one well-constructed item (jacket, shoes, jeans) that will last 5+ years instead of buying fast fashion that falls apart in months.",
                'estimated_cost': '$80 – $180',
                'tags': ['shopping', 'quality', 'investment', 'sustainable'],
            },
        ],
        'tier4': [
            {
                'title': 'Tech or Hobby Gear Upgrade',
                'description': "Invest in something that directly improves your productivity or a hobby you love — headphones, a nice keyboard, camera accessories.",
                'estimated_cost': '$150 – $400',
                'tags': ['shopping', 'technology', 'investment'],
            },
        ],
    },

    'arts': {
        'tier1': [
            {
                'title': 'Free Museum Day',
                'description': "Most cities have museums with free days or donation-based admission. Many are free on the first Sunday of the month.",
                'estimated_cost': '$0 – $5',
                'tags': ['arts', 'culture', 'learning'],
            },
            {
                'title': 'Start a Sketch Journal',
                'description': "Buy a cheap sketchbook and some pencils and start drawing daily, even just for 10 minutes. Creativity is a muscle.",
                'estimated_cost': '$5 – $15',
                'tags': ['arts', 'creative', 'home'],
            },
        ],
        'tier2': [
            {
                'title': 'Attend a Gallery Opening',
                'description': "Local gallery openings are often free, include refreshments, and are a great way to engage with your local art scene.",
                'estimated_cost': '$0 – $20',
                'tags': ['arts', 'culture', 'social'],
            },
            {
                'title': 'Pottery Drop-in Session',
                'description': "Many pottery studios offer walk-in sessions. Learning to throw clay is surprisingly meditative and fun.",
                'estimated_cost': '$30 – $55',
                'tags': ['arts', 'creative', 'hands-on'],
            },
        ],
        'tier3': [
            {
                'title': 'Local Theater or Orchestra Performance',
                'description': "Community theaters and local orchestras offer world-class performances at a fraction of Broadway prices.",
                'estimated_cost': '$30 – $90',
                'tags': ['arts', 'culture', 'live'],
            },
            {
                'title': 'Enroll in an Art Class Series',
                'description': "Sign up for a 4–6 week class in watercolor, life drawing, printmaking, or photography. Learn a new creative skill.",
                'estimated_cost': '$80 – $180',
                'tags': ['arts', 'creative', 'skill-building'],
            },
        ],
        'tier4': [
            {
                'title': 'Weekend Art Workshop',
                'description': "Sign up for an intensive 2-day workshop in a medium you want to master. Immersive learning accelerates skills dramatically.",
                'estimated_cost': '$200 – $450',
                'tags': ['arts', 'skill-building', 'experience'],
            },
        ],
    },

    'outdoor': {
        'tier1': [
            {
                'title': 'Sunrise or Sunset Hike',
                'description': "Wake up early and hike to a local viewpoint before sunrise. The silence, colors, and sense of accomplishment are hard to beat.",
                'estimated_cost': '$0 – $5',
                'tags': ['outdoor', 'nature', 'free'],
            },
        ],
        'tier2': [
            {
                'title': 'Kayak or Canoe Rental',
                'description': "Rent a kayak or canoe for 2–3 hours at a local lake or river. Peaceful, great exercise, no experience needed.",
                'estimated_cost': '$25 – $60',
                'tags': ['outdoor', 'water', 'adventure'],
            },
            {
                'title': 'Indoor Rock Climbing',
                'description': "Most climbing gyms have beginner-friendly bouldering walls. Day passes often include shoe rentals. Full-body workout that's addictive.",
                'estimated_cost': '$20 – $35',
                'tags': ['outdoor', 'fitness', 'skill-building'],
            },
        ],
        'tier3': [
            {
                'title': 'Guided Outdoor Adventure',
                'description': "Book a guided kayak, mountain bike, or climbing trip. Learn from a professional guide and explore somewhere new.",
                'estimated_cost': '$75 – $150',
                'tags': ['outdoor', 'adventure', 'guided'],
            },
        ],
        'tier4': [
            {
                'title': 'Invest in Quality Outdoor Gear',
                'description': "Buy a solid piece of gear you'll use for years: a proper tent, sleeping bag, hiking boots, or a packable rain jacket.",
                'estimated_cost': '$150 – $400',
                'tags': ['outdoor', 'gear', 'investment'],
            },
        ],
    },

    'technology': {
        'tier1': [
            {
                'title': 'Take an Online Course',
                'description': "Udemy courses go on sale for $10–15 regularly. Learn Python, web dev, data analysis, design — whatever skill is on your list.",
                'estimated_cost': '$0 – $15',
                'tags': ['technology', 'learning', 'skill-building'],
            },
        ],
        'tier2': [
            {
                'title': 'Upgrade a Practical Tech Accessory',
                'description': "A quality phone stand, ergonomic mouse, USB-C hub, or mechanical keyboard makes your daily setup noticeably better.",
                'estimated_cost': '$20 – $60',
                'tags': ['technology', 'practical', 'daily-use'],
            },
        ],
        'tier3': [
            {
                'title': 'Add a Smart Home Device',
                'description': "A smart plug, LED light strip system, or voice assistant can make your home more comfortable and energy-efficient.",
                'estimated_cost': '$30 – $100',
                'tags': ['technology', 'home', 'convenience'],
            },
        ],
        'tier4': [
            {
                'title': 'Invest in Quality Audio',
                'description': "Good headphones or earbuds transform focus sessions, workouts, and commutes. It's one of the highest-impact tech purchases you can make.",
                'estimated_cost': '$100 – $350',
                'tags': ['technology', 'quality', 'investment'],
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Engine Logic
# ---------------------------------------------------------------------------

def get_budget_tier(remaining: float) -> str:
    """
    Convert a dollar amount into a recommendation tier label.

    LEARNING: This is a pure function — given the same input, it always
    returns the same output and has no side effects. Pure functions are
    easy to test and reason about.
    """
    if remaining < 25:
        return 'tier1'
    elif remaining < 75:
        return 'tier2'
    elif remaining < 200:
        return 'tier3'
    else:
        return 'tier4'


def get_recommendations(interests: list, remaining_budget: float) -> list:
    """
    Generate a list of recommendations based on interests and remaining budget.

    Args:
        interests:         List of interest strings (e.g., ['fitness', 'dining'])
        remaining_budget:  How much the user has left in their monthly budget

    Returns:
        List of recommendation dicts with added metadata

    LEARNING — The ** (spread) operator:
        {**rec, 'extra_key': 'value'} creates a new dict with all keys
        from rec PLUS the extra key. It's like Object.assign() in JavaScript.
    """
    tier = get_budget_tier(remaining_budget)

    # If the user hasn't set interests, show a sensible default set
    active_interests = interests if interests else ['dining', 'entertainment', 'outdoor']

    results = []
    for interest in active_interests:
        if interest not in RECOMMENDATIONS:
            continue  # Skip unknown interest categories

        interest_recs = RECOMMENDATIONS[interest]

        # Try to find recommendations for the appropriate tier.
        # Fall back to tier1 if the current tier has no entries for this interest.
        tier_list = interest_recs.get(tier) or interest_recs.get('tier1', [])

        for rec in tier_list:
            results.append({
                **rec,                           # All fields from the recommendation
                'interest_category': interest,   # Which interest triggered this
                'budget_tier': tier,             # Which tier was used
            })

    return results
