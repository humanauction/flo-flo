"""Seed database with test headlines"""
from app.db.database import SessionLocal
from app.models.headline import Headline


# Test headlines
test_headlines = [
    {
        "text": "Florida man arrested for teaching squirrels to "
                "attack his ex-girlfriend",
        "is_real": True,
        "source_url": "https://www.clickorlando.com/news/2019/04/18/florida-man-accused-of-training-squirrels-to-attack/"
    },
    {
        "text": "Florida man throws alligator through drive-thru window",
        "is_real": True,
        "source_url": "https://www.nbcnews.com/news/us-news/florida-man-threw-alligator-through-drive-thru-window-police-say-n856546"
    },
    {
        "text": "Florida man attempts to pay for McDonald's with bag of weed",
        "is_real": True,
        "source_url": "https://www.palmbeachpost.com/story/news/crime/2018/03/02/florida-man-tried-to-pay-for-mcdonalds-order-with-weed-cops-say/9875026007/"
    },
    {
        "text": "Florida man caught riding manatee while "
                "dressed as Santa Claus",
        "is_real": False,
        "source_url": None
    },
    {
        "text": "Florida man builds working rocket ship from "
                "reclaimed Waffle House materials",
        "is_real": False,
        "source_url": None
    },
]

db = SessionLocal()

try:
    for headline_data in test_headlines:
        # Check if already exists
        existing = db.query(Headline).filter(Headline.text == headline_data["text"]).first()
        if not existing:
            headline = Headline(**headline_data)
            db.add(headline)
            print(f"✅ Added: {headline_data['text'][:60]}...")
        else:
            print(f"⏭️  Skipped (exists): {headline_data['text'][:60]}...")

    db.commit()
    print(f"\n🎉 Seeding complete! {len(test_headlines)} headlines processed.")

except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
