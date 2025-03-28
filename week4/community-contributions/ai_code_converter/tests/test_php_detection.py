"""Test module for PHP language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_php_detection():
    """Test the PHP language detection functionality."""
    detector = LanguageDetector()
    
    # Sample PHP code
    php_code = r"""
<?php
// Define namespace
namespace App\Controllers;

// Import classes
use App\Models\User;
use App\Services\AuthService;
use App\Exceptions\AuthException;

/**
 * Authentication Controller
 * 
 * Handles user authentication functionality
 */
class AuthController
{
    private $authService;
    
    /**
     * Constructor
     */
    public function __construct(AuthService $authService)
    {
        $this->authService = $authService;
    }
    
    /**
     * Login user
     */
    public function login($request)
    {
        // Get request data
        $email = $request->input('email');
        $password = $request->input('password');
        $remember = $request->input('remember', false);
        
        // Validate input
        if (empty($email) || empty($password)) {
            return [
                'status' => 'error',
                'message' => 'Email and password are required'
            ];
        }
        
        try {
            // Attempt to login
            $user = $this->authService->authenticate($email, $password);
            
            // Create session
            $_SESSION['user_id'] = $user->id;
            
            // Set remember me cookie if requested
            if ($remember) {
                $token = $this->authService->createRememberToken($user->id);
                setcookie('remember_token', $token, time() + 86400 * 30, '/');
            }
            
            return [
                'status' => 'success',
                'user' => $user
            ];
        } catch (AuthException $e) {
            return [
                'status' => 'error',
                'message' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Register new user
     */
    public function register($request)
    {
        // Get request data
        $name = $request->input('name');
        $email = $request->input('email');
        $password = $request->input('password');
        
        // Validate input
        if (empty($name) || empty($email) || empty($password)) {
            return [
                'status' => 'error',
                'message' => 'All fields are required'
            ];
        }
        
        // Check if email already exists
        $existingUser = User::findByEmail($email);
        if ($existingUser) {
            return [
                'status' => 'error',
                'message' => 'Email already registered'
            ];
        }
        
        // Create user
        $user = new User();
        $user->name = $name;
        $user->email = $email;
        $user->password = password_hash($password, PASSWORD_DEFAULT);
        $user->save();
        
        // Login user
        $_SESSION['user_id'] = $user->id;
        
        return [
            'status' => 'success',
            'user' => $user
        ];
    }
    
    /**
     * Logout user
     */
    public function logout()
    {
        // Clear session
        unset($_SESSION['user_id']);
        session_destroy();
        
        // Clear remember token cookie if it exists
        if (isset($_COOKIE['remember_token'])) {
            setcookie('remember_token', '', time() - 3600, '/');
        }
        
        return [
            'status' => 'success',
            'message' => 'Logged out successfully'
        ];
    }
    
    /**
     * Get current user profile
     */
    public function profile()
    {
        if (!isset($_SESSION['user_id'])) {
            return [
                'status' => 'error',
                'message' => 'Not authenticated'
            ];
        }
        
        $user = User::find($_SESSION['user_id']);
        
        return [
            'status' => 'success',
            'user' => $user
        ];
    }
}
?>
"""
    
    # Test the detection
    assert detector.detect_php(php_code) == True
    assert detector.detect_language(php_code) == "PHP"
    
    # Check validation
    valid, _ = detector.validate_language(php_code, "PHP")
    assert valid == True


if __name__ == "__main__":
    test_php_detection()
    print("All PHP detection tests passed!")
