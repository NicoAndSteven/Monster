import requests
import time
import os

BASE_URL = "http://localhost:8000/api"

def log(msg):
    print(f"[TEST] {msg}")

def run_tests():
    # 1. Create Novel
    novel_id = f"test_{int(time.time())}"
    log(f"Creating Novel with ID: {novel_id}")
    res = requests.post(f"{BASE_URL}/novels", json={
        "id": novel_id,
        "title": "Automated Test Novel",
        "description": "A novel created by test script"
    })
    assert res.status_code == 200, f"Create Novel failed: {res.text}"
    log("Novel created successfully.")

    # 2. List Novels
    res = requests.get(f"{BASE_URL}/novels")
    assert res.status_code == 200
    novels = res.json()
    assert any(n['id'] == novel_id for n in novels), "Novel not found in list"
    log("Novel list verification passed.")

    # 3. Create Asset (Character)
    log("Creating Character Asset...")
    asset_id = "char_001"
    res = requests.post(f"{BASE_URL}/novels/{novel_id}/assets", json={
        "id": asset_id,
        "type": "character",
        "name": "Test Hero",
        "role": "Protagonist",
        "tags": ["brave", "smart"],
        "img": ""
    })
    assert res.status_code == 200, f"Create Asset failed: {res.text}"
    
    # Verify Asset List
    res = requests.get(f"{BASE_URL}/novels/{novel_id}/assets")
    assets = res.json()
    assert len(assets) == 1
    assert assets[0]['name'] == "Test Hero"
    log("Asset creation and listing passed.")

    # 4. Create Chapter 1
    log("Creating Chapter 1...")
    res = requests.put(f"{BASE_URL}/novels/{novel_id}/chapters/1", json={
        "content": "<p>This is chapter 1 content. The hero woke up.</p>"
    })
    assert res.status_code == 200
    log("Chapter 1 created.")

    # 5. Create Chapter 2 (AI Generation Test)
    log("Generating Chapter 2 with AI (Mock)...")
    res = requests.post(f"{BASE_URL}/novels/{novel_id}/generate", json={
        "chapter_num": 2,
        "prompt": "The hero goes to adventure.",
        "mode": "api",
        "include_assets": True,
        "context_window": 500
    })
    assert res.status_code == 200
    data = res.json()
    content = data['chapter']['content']
    log(f"Generated Content: {content[:100]}...")
    
    # Check if context was injected (The mock response usually reflects inputs or generic text, 
    # but we just need to ensure the endpoint works and returns content)
    assert len(content) > 0
    log("AI Generation passed.")

    # 6. Export Novel
    log("Exporting Novel...")
    res = requests.get(f"{BASE_URL}/novels/{novel_id}/export")
    assert res.status_code == 200
    assert res.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    # Save to disk to verify it's a real file
    with open("test_export.docx", "wb") as f:
        f.write(res.content)
    assert os.path.exists("test_export.docx")
    assert os.path.getsize("test_export.docx") > 0
    log("Export passed. File saved to test_export.docx")

    # 7. Clean up
    log("Cleaning up...")
    res = requests.delete(f"{BASE_URL}/novels/{novel_id}")
    assert res.status_code == 200
    
    # Verify deletion
    res = requests.get(f"{BASE_URL}/novels")
    novels = res.json()
    assert not any(n['id'] == novel_id for n in novels), "Novel was not deleted"
    
    # Clean up local file
    if os.path.exists("test_export.docx"):
        os.remove("test_export.docx")
        
    log("Cleanup passed.")
    log("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        exit(1)
