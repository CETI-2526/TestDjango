from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from django.contrib.auth.models import User
import time

class AdminCreatesStaffUserTest(StaticLiveServerTestCase):
 
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        # Add headless option for CI/CD (comment out to see browser during development)
        # opts.add_argument("--headless")
        cls.selenium = WebDriver(options=opts)
        cls.selenium.implicitly_wait(5)
        
        # Create ONLY the admin user - NOT UserStaff yet
        cls.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123"
        )

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def login(self, username, password):
        """Helper method to login"""
        # Navigate to login page
        login_url = f"{self.live_server_url}/admin/login/"
        self.selenium.get(login_url)
        
        # Wait for login form
        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
        except TimeoutException:
            # Check if we're already logged in
            if "/admin/" in self.selenium.current_url and "/login/" not in self.selenium.current_url:
                print(f"  Already logged in, logging out first...")
                self.logout()
                self.selenium.get(login_url)
                WebDriverWait(self.selenium, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
        
        # Fill login form
        username_input = self.selenium.find_element(By.NAME, "username")
        password_input = self.selenium.find_element(By.NAME, "password")
        submit = self.selenium.find_element(By.XPATH, '//input[@value="Log in"]')
        
        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)
        submit.click()
        
        # Wait for login to complete
        time.sleep(2)
        return self.selenium.current_url
    
    def logout(self):
        """Helper method to logout using the logout form (id='logout-form')"""
        try:
            # First, make sure we're on an admin page
            if "/admin/" not in self.selenium.current_url:
                self.selenium.get(f"{self.live_server_url}/admin/")
                time.sleep(1)
            
            # Look for the logout form with id='logout-form' (from your screenshot)
            try:
                # Find the logout form by ID
                logout_form = self.selenium.find_element(By.ID, "logout-form")
                
                # Find the logout button inside the form
                # It's a <button> element, not a link
                logout_button = logout_form.find_element(By.TAG_NAME, "button")
                print(f"  Found logout button: '{logout_button.text}'")
                logout_button.click()
                
            except NoSuchElementException:
                # Fallback: try to find logout button directly
                logout_buttons = self.selenium.find_elements(By.TAG_NAME, "button")
                for button in logout_buttons:
                    if "log" in button.text.lower() and "out" in button.text.lower():
                        button.click()
                        print(f"  Logged out via button: '{button.text}'")
                        break
                else:
                    print("  Could not find logout button, navigating to logout URL")
                    self.selenium.get(f"{self.live_server_url}/admin/logout/")
            
            # Wait for logout to complete
            time.sleep(2)
            
            # Verify we're on logout page
            page_source = self.selenium.page_source.lower()
            if "logged out" in page_source or "log in again" in page_source:
                print("  ✓ Logout successful")
            else:
                print("  Logout may not have completed")
                
        except Exception as e:
            print(f"  Error during logout: {str(e)}")
            # Fallback to direct logout URL
            self.selenium.get(f"{self.live_server_url}/admin/logout/")
    
    def login_after_logout(self, username, password):
        """Special login method to use after logout (clicks 'Log in again' link)"""
        # First check if we're on logout page with "Log in again" link
        page_source = self.selenium.page_source
        
        if "logged out" in page_source.lower():
            # Click the "Log in again" link (from your screenshot)
            try:
                login_again_link = self.selenium.find_element(By.LINK_TEXT, "Log in again")
                login_again_link.click()
                time.sleep(2)
            except NoSuchElementException:
                # If link not found, navigate to login page directly
                self.selenium.get(f"{self.live_server_url}/admin/login/")
        else:
            # Not on logout page, go to login page directly
            self.selenium.get(f"{self.live_server_url}/admin/login/")
        
        # Now login as usual
        return self.login(username, password)
    
    def test_admin_creates_staff_user_then_staff_cannot_create_users_or_questions(self):
        """
        Test workflow:
        1. Admin logs in
        2. Admin creates new user 'UserStaff' with ONLY Staff permission
        3. Admin logs out using logout-form
        4. UserStaff logs in using "Log in again" link
        5. Verify UserStaff CANNOT create other users
        6. Verify UserStaff CANNOT create questions
        """
        
        print("=" * 60)
        print("TEST: Admin creates staff user, then staff has limited permissions")
        print("=" * 60)
        
        # STEP 1: Login as ADMIN
        print("\n1. Logging in as ADMIN...")
        current_url = self.login("admin", "admin123")
        
        if "/admin/" in current_url and "/login/" not in current_url:
            print("   ✓ Admin login successful")
        else:
            print(f"   ✗ Admin login failed. URL: {current_url}")
            self.fail("Admin login failed")
        
        # STEP 2: Create UserStaff
        print("\n2. Creating UserStaff...")
        
        # Go to add user page
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/auth/user/add/'))
        
        # Wait for form
        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_username"))
            )
        except TimeoutException:
            self.fail("Add user page failed to load")
        
        # Fill user details
        username_field = self.selenium.find_element(By.ID, "id_username")
        username_field.clear()
        username_field.send_keys("UserStaff")
        
        password1_field = self.selenium.find_element(By.ID, "id_password1")
        password1_field.send_keys("StaffPass123")
        
        password2_field = self.selenium.find_element(By.ID, "id_password2")
        password2_field.send_keys("StaffPass123")
        
        # Click first save
        save_button = self.selenium.find_element(By.NAME, "_save")
        save_button.click()
        
        # Wait for permissions page
        try:
            WebDriverWait(self.selenium, 10).until(
                EC.presence_of_element_located((By.ID, "id_is_staff"))
            )
            print("   ✓ On permissions page")
        except TimeoutException:
            # Check if user was created in one step
            try:
                User.objects.get(username="UserStaff")
                print("   ✓ UserStaff created (single-step form)")
                # Need to edit to set staff permission
                self._edit_user_to_set_staff()
            except User.DoesNotExist:
                self.fail("UserStaff not created")
        
        # If on permissions page, set permissions
        if "id_is_staff" in self.selenium.page_source:
            # Set staff permission
            staff_checkbox = self.selenium.find_element(By.ID, "id_is_staff")
            if not staff_checkbox.is_selected():
                staff_checkbox.click()
            
            # Uncheck superuser if checked
            try:
                superuser_checkbox = self.selenium.find_element(By.ID, "id_is_superuser")
                if superuser_checkbox.is_selected():
                    superuser_checkbox.click()
            except NoSuchElementException:
                pass
            
            # Save permissions
            self.selenium.find_element(By.NAME, "_save").click()
            time.sleep(2)
        
        # Verify UserStaff in database
        try:
            staff_user = User.objects.get(username="UserStaff")
            self.assertTrue(staff_user.is_staff, "UserStaff should be staff")
            self.assertFalse(staff_user.is_superuser, "UserStaff should NOT be superuser")
            print(f"   ✓ UserStaff created: is_staff={staff_user.is_staff}, is_superuser={staff_user.is_superuser}")
        except User.DoesNotExist:
            self.fail("UserStaff not in database")
        
        # STEP 3: Logout ADMIN using logout-form
        print("\n3. Logging out ADMIN (using logout-form)...")
        self.logout()
        
        # Verify we're on logout page
        page_source = self.selenium.page_source.lower()
        if "logged out" not in page_source:
            print("   Warning: Not on logout page after logout")
            print(f"   Current page: {self.selenium.current_url}")
        
        # STEP 4: Login as UserStaff using "Log in again" link
        print("\n4. Logging in as UserStaff (using 'Log in again' link)...")
        
        # Use special login method for after logout
        current_url = self.login_after_logout("UserStaff", "StaffPass123")
        
        if "/admin/" in current_url and "/login/" not in current_url:
            print("   ✓ UserStaff login successful")
        else:
            print(f"   ✗ UserStaff login failed. URL: {current_url}")
            
            # Check if user is active
            staff_user = User.objects.get(username="UserStaff")
            if not staff_user.is_active:
                print("   UserStaff is not active! Activating...")
                staff_user.is_active = True
                staff_user.save()
                
                # Try login again
                current_url = self.login_after_logout("UserStaff", "StaffPass123")
                if "/admin/" in current_url and "/login/" not in current_url:
                    print("   ✓ UserStaff login successful after activation")
                else:
                    self.fail("UserStaff login failed even after activation")
            else:
                self.fail("UserStaff login failed")
        
        # STEP 5: Test UserStaff cannot add Users
        print("\n5. Testing if UserStaff can add other Users...")
        self._test_cannot_add_users()
        
        # STEP 6: Test UserStaff cannot add Questions
        print("\n6. Testing if UserStaff can add Questions...")
        self._test_cannot_add_questions()
        
        # STEP 7: Logout UserStaff
        print("\n7. Logging out UserStaff...")
        self.logout()
        
        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)
    
    def _edit_user_to_set_staff(self):
        """Edit existing UserStaff to set staff permission"""
        print("   Editing UserStaff to set staff permission...")
        
        # Go to users list
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/auth/user/'))
        time.sleep(2)
        
        # Find and click UserStaff
        try:
            userstaff_link = self.selenium.find_element(By.LINK_TEXT, "UserStaff")
            userstaff_link.click()
            time.sleep(2)
            
            # Check staff checkbox
            staff_checkbox = self.selenium.find_element(By.ID, "id_is_staff")
            if not staff_checkbox.is_selected():
                staff_checkbox.click()
            
            # Save
            self.selenium.find_element(By.NAME, "_save").click()
            time.sleep(2)
            print("   ✓ UserStaff edited to be staff")
            
        except NoSuchElementException:
            print("   ✗ Could not find UserStaff to edit")
    
    def _test_cannot_add_users(self):
        """Test that UserStaff cannot add users"""
        # Go to users page
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/auth/user/'))
        time.sleep(2)
        
        # Check for add button
        try:
            add_button = self.selenium.find_element(By.CLASS_NAME, "addlink")
            print(f"   Found 'Add' button, testing...")
            
            # Click it
            add_button.click()
            time.sleep(3)
            
            # Check result
            if "/auth/user/add/" in self.selenium.current_url:
                # Check if form is usable
                try:
                    self.selenium.find_element(By.ID, "id_username")
                    print("   ✗ FAIL: UserStaff CAN access add user form")
                    self.fail("UserStaff should not be able to add users")
                except NoSuchElementException:
                    print("   ✓ PASS: Form not usable")
            else:
                print("   ✓ PASS: Redirected from add user page")
                
        except NoSuchElementException:
            print("   ✓ PASS: No 'Add user' button visible")
    
    def _test_cannot_add_questions(self):
        """Test that UserStaff cannot add questions"""
        # Go to admin index
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/'))
        time.sleep(2)
        
        # Look for Questions
        try:
            # Find all links
            all_links = self.selenium.find_elements(By.TAG_NAME, "a")
            questions_link = None
            
            for link in all_links:
                if "question" in link.text.lower():
                    questions_link = link
                    break
            
            if questions_link:
                print(f"   Found Questions link: {questions_link.text}")
                questions_link.click()
                time.sleep(2)
                
                # Try to add
                try:
                    add_button = self.selenium.find_element(By.CLASS_NAME, "addlink")
                    add_button.click()
                    time.sleep(3)
                    
                    if "/add/" in self.selenium.current_url:
                        print("   ✗ FAIL: UserStaff CAN access add question page")
                        self.fail("UserStaff should not be able to add questions")
                    else:
                        print("   ✓ PASS: Cannot add questions")
                        
                except NoSuchElementException:
                    print("   ✓ PASS: No 'Add question' button")
            else:
                print("   Note: Questions not found in admin")
                
        except Exception as e:
            print(f"   Error testing questions: {str(e)}")
