import asyncio
import os
from core.config import load_config
from modules.facebook_broadcaster import FacebookBroadcaster

async def main():
    print("Loading config...")
    config = load_config()
    
    print("Initializing Facebook Broadcaster...")
    broadcaster = FacebookBroadcaster(
        page_id=config.facebook_page_id,
        access_token=config.facebook_access_token
    )
    
    story = """ایک چھوٹی سی بستی تھی— کراچی کے مضافات میں، جہاں ہر گھر مٹی اور امید کی خوشبو سے بسا ہوا تھا۔ صبح کی پہلی کرن جب مسجد کے مینار پر پڑتی، تو پورا گاؤں جیسے ایک سر میں گنگنانے لگتا۔

ملکہ بی ایک عام سی عورت تھی، جو اپنے چار بچوں کے ساتھ ایک چھوٹے سے گھر میں رہتی تھی۔ اس کا شوہر، حاجی صاحب، روزانہ صبح سویرے درگاہ پر جاتے اور شام کو واپس آتے، اپنے ساتھ کچھ پیسے اور ایک بڑی سی مسکراہٹ لاتے۔

لیکن شام کو جب سورج ڈھلنے لگا، تو حاجی صاحب واپس نہیں لوٹے۔ شہر میں افواہیں پھیلنے لگیں کہ کسی ٹریفک حادثے میں ان کی گاڑی الٹ گئی تھی۔ ملکہ بی کی سانس رک گئی، دل جیسے تھم سا گیا۔ وہ درگاہ کی طرف دوڑی...

جب وہ وہاں پہنچی، تو اس نے دیکھا کہ حاجی صاحب کچھ لوگوں کی مدد کر رہے تھے—ایک زخمی بچے کو ہسپتال لے جانے کی کوشش کر رہے تھے۔ وہ اپنی جان خطرے میں ڈال کر دوسروں کی جان بچا رہے تھے۔

عید کی رات، جب پورا شہر چاند کی روشنی میں نہا رہا تھا، حاجی صاحب نے اپنی تھکی ہوئی آنکھوں سے ملکہ بی کی روٹیاں کھاتے ہوئے دیکھا۔ وہ اتنی سادہ تھیں، لیکن ان کی روٹیوں میں ذائقہ اور پیار دونوں تھے۔"""

    image_path = r"C:\Users\AKR-LAPTOP\Desktop\Facebook auto posting\omni_channel_bot\assets\generated_images\post_20260806_004015_587.png"
    
    package = {
        "story_text": story,
        "image_path": image_path
    }
    
    print(f"Attempting to post to Facebook Page: {config.facebook_page_id}")
    success = await broadcaster.post(package)
    
    if success:
        print("✅ SUCCESS! The post is live on your Facebook Page!")
    else:
        print("❌ FAILED! Check logs for errors.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
