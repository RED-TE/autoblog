try:
    with open("test_log.txt", "w") as f:
        f.write("Hello World! Python is working.")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
