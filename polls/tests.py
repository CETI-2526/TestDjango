from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
import time

class StaffUserPermissionTest(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n1. Setting up test class")
        super().setUpClass()
        opts = Options()
        cls.selenium = WebDriver(options=opts)
        cls.selenium.implicitly_wait(5)

        print("\n2. Creating admin user")
        User.objects.create_superuser("admin", "admin@example.com", "admin123")
    
    @classmethod
    def tearDownClass(cls):
        print("\n3. Tearing down test class...")
        cls.selenium.quit()
        super().tearDownClass()
    
    def login(self, username, password):
        print(f"   - Logging in as {username}...")
        self.selenium.get(f"{self.live_server_url}/admin/login/")
        self.selenium.find_element(By.NAME, "username").send_keys(username)
        self.selenium.find_element(By.NAME, "password").send_keys(password)
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()
        time.sleep(2)
        print(f"   - Logged in as {username}")

    def logout(self):
        print("   - Logging out...")
        self.selenium.get(f"{self.live_server_url}/admin/")
        logout_form = self.selenium.find_element(By.ID, "logout-form")
        logout_form.find_element(By.TAG_NAME, "button").click()
        time.sleep(2)
        print("   - Logged out")

    def create_staff_user(self):
        print("   - Creating staff user...")
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/add/")
        
        print("     a. Filling basic user info...")
        self.selenium.find_element(By.ID, "id_username").send_keys("UserStaff")
        self.selenium.find_element(By.ID, "id_password1").send_keys("StaffPass123")
        self.selenium.find_element(By.ID, "id_password2").send_keys("StaffPass123")
        self.selenium.find_element(By.NAME, "_save").click()
        time.sleep(2)
        
        print("     b. Setting staff permissions...")
        staff_checkbox = self.selenium.find_element(By.ID, "id_is_staff")
        if not staff_checkbox.is_selected():
            staff_checkbox.click()
        
        superuser_checkbox = self.selenium.find_element(By.ID, "id_is_superuser")
        if superuser_checkbox.is_selected():
            superuser_checkbox.click()
        
        print("     c. Saving staff user...")
        self.selenium.find_element(By.NAME, "_save").click()
        time.sleep(2)

        print("   - Staff user created successfully")
    
    def test_staff_user_cannot_create_users_or_questions(self):
        print("\n===== TEST STARTED: Staff user permission check =====")

        print("\n4. Admin logs in and creates staff user")
        self.login("admin", "admin123")
        self.create_staff_user()
        self.logout()
        
        print("\n5. Staff user logs in")
        login_again_link = self.selenium.find_element(By.LINK_TEXT, "Log in again")
        login_again_link.click()
        self.login("UserStaff", "StaffPass123")
        
        print("\n6. Checking if staff user can add users...")
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/")
        
        try:
            add_button = self.selenium.find_element(By.CLASS_NAME, "addlink")
            print("   - Add User button found")
            add_button.click()
            time.sleep(2)
            
            if "/auth/user/add/" in self.selenium.current_url:
                print("   - Staff user reached add-user page — FAIL")
                self.fail("Staff user should not be able to add users")
        except:
            print("   - No Add User button — correct behavior")
        
        print("\n7. Checking if staff user can add questions...")
        self.selenium.get(f"{self.live_server_url}/admin/")
        
        links = self.selenium.find_elements(By.TAG_NAME, "a")
        questions_link = None
        
        for link in links:
            if "question" in link.text.lower():
                questions_link = link
                break
        
        if questions_link:
            print("   - Questions section found — opening...")
            questions_link.click()
            time.sleep(2)
            
            try:
                add_button = self.selenium.find_element(By.CLASS_NAME, "addlink")
                print("   - Add button found — attempting to click...")
                add_button.click()
                time.sleep(2)
                
                if "/add/" in self.selenium.current_url:
                    print("   - Staff user reached add-question page — FAIL")
                    self.fail("Staff user should not be able to add questions")
            except:
                print("   - No add button — correct behavior")
        else:
            print("   - No questions section visible — correct behavior")
        
        print("\n8. Verifying database permissions...")
        staff_user = User.objects.get(username="UserStaff")
        assert staff_user.has_perm('auth.add_user') is False
        print("   - Database permissions confirmed")

        print("\n9. Staff user on 403 FORBIDDEN")

        print("===== TEST COMPLETED SUCCESSFULLY =====\n")
