import asyncio
import os
import sys

try:
    from BingImageCreator import ImageGenAsync
except ImportError:
    print("Error: BingImageCreator not installed. Run 'pip install BingImageCreator'")
    sys.exit(1)

async def test_bing_image(cookie: str, prompt: str):
    print("Initializing Bing Image Creator with your cookie...")
    # Initialize the generator
    async_gen = ImageGenAsync(cookie)
    
    print(f"Sending prompt to Bing: '{prompt}'")
    try:
        # Generate images (Bing usually returns a list of 4 image URLs)
        images = await async_gen.get_images(prompt)
        
        print("\nSUCCESS! Bing generated the following image URLs:")
        for idx, url in enumerate(images):
            print(f"Image {idx+1}: {url}")
            
        print("\nDownloading the first image for you...")
        # Save it to the current directory
        await async_gen.save_images([images[0]], output_dir="./")
        print("Image downloaded as a .jpeg file in this folder!")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        print("This usually means your _U cookie is invalid, expired, or your temp account ran out of Bing 'Boosts'.")

if __name__ == "__main__":
    # Replace this string with your actual _U cookie from Edge
    YOUR_BING_COOKIE = "1PxaGtRrbGAWLJMynHfjQiCe7QmzabFmBx2Z9AlvrydjT-3Yd831Qloa5LA09eWV-os2OhpsOn-z322_5BD27IzAqXz_bihIz7Z-_zLtkZnB_8EMn3QFNFnNUtit3dd9ZgzyZIiemd3W80im7Mu6kKN0iSoMIJWB161y6p0ZimRd9MG7l0rrElRbUNMYrLRRsFtpJ8hg6YoXSniAhLo8JCDGgDv0Fjfmb-_pulTlGVpw"
    
    if YOUR_BING_COOKIE == "REPLACE_ME_WITH_YOUR_U_COOKIE":
        print("Please edit this file and put your actual _U cookie in the YOUR_BING_COOKIE variable.")
        sys.exit(1)
        
    test_prompt = "A cinematic, 8K hyperrealistic photo of a futuristic robotic news anchor reporting breaking news from a glowing cyberpunk city desk."
    
    asyncio.run(test_bing_image(YOUR_BING_COOKIE, test_prompt))
