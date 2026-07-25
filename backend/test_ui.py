from playwright.sync_api import sync_playwright
import time
import re

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch()
        page = browser.new_page()

        print("Navigating to Ouvidoria...")
        page.goto("http://localhost:5173/ouvidoria")

        # 1. Fill out the form
        print("Filling out ticket form...")
        page.select_option("select", "infrastructure")
        page.fill("input[placeholder='Ex.: 2025.2']", "2024.1")
        page.fill("textarea", "O ar condicionado da sala de estudos está quebrado desde a semana passada.")

        # 2. Submit the form
        print("Submitting the form...")
        page.click("button:has-text('Enviar ticket')")

        # 3. Wait for success and extract protocol
        page.wait_for_selector(".anon-success")
        success_text = page.locator(".anon-success").inner_text()
        print(f"Success text: {success_text}")

        # Extract protocol from success_text (e.g. "Protocolo: ABCD1234EF")
        # Let's find a 10 char alphanumeric string
        match = re.search(r'([A-Z0-9]{10})', success_text)
        protocol = ""
        if match:
            protocol = match.group(1)
            print(f"✅ Extracted Protocol: {protocol}")
        else:
            print("❌ Failed to extract protocol!")
            return

        # 4. Search for the protocol
        print(f"Searching for protocol: {protocol}")
        page.fill("input[placeholder='Digite seu nº de protocolo…']", protocol)
        page.click("button:has-text('Consultar')")

        # 5. Wait for result
        page.wait_for_selector(".msg-body")
        result_text = page.locator(".msg-body").inner_text()
        print("Result card contents:")
        print(result_text)

        # 6. Add complement
        print("Adding a complement...")
        page.fill("textarea[placeholder='Escreva a informação adicional…']", "Aliás, a luz também está piscando.")
        page.click("button:has-text('Enviar complemento')")

        # Wait for update
        time.sleep(1) # wait for DOM update
        updated_text = page.locator(".msg-body").inner_text()
        print("Updated result card contents:")
        print(updated_text)

        print("✅ E2E UI Tests completed successfully!")
        browser.close()

if __name__ == "__main__":
    run()
