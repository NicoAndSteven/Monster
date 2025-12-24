from gradio_client import Client, handle_file

client = Client("Tongyi-MAI/Z-Image-Turbo")
result = client.predict(
	prompt="a boy sit in the classroom where full of piano",
	resolution="1024x1024 ( 1:1 )",
	seed=42,
	steps=8,
	shift=3,
	random_seed=True,
	gallery_images=[],
	api_name="/generate"
)
print(result)