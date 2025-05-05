import React, { useState, useRef, useEffect } from 'react';
import {
    IoMdNotificationsOutline,
    IoMdArrowDropdown,
    IoMdArrowDropup,
    IoMdLogOut,
    IoMdTrash,
    IoMdColorPalette,
    IoMdPerson,
    IoMdLock,
    IoMdGlobe,
    IoMdMail,
    IoMdHelpCircle,
    IoMdInformationCircle
} from "react-icons/io";
import { IoClose, IoSettingsOutline } from "react-icons/io5";
import { CiLock, CiUser } from "react-icons/ci";
import { useFrappeAuth, useFrappeFileUpload, useFrappeGetDoc, useFrappeUpdateDoc } from 'frappe-react-sdk';
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { ToastContainer } from 'react-toastify';


function Settings({onClose}) {
    const { currentUser } = useFrappeAuth();
    const { updateDoc } = useFrappeUpdateDoc();
    const { upload } = useFrappeFileUpload();

    console.log("curent use",currentUser);
    const { data: userDoc, isLoading, error } = useFrappeGetDoc(
        "User",
        currentUser || "Guest" // fallback to a dummy value to avoid hook breaking
      );
    
    const [activeTab, setActiveTab] = useState('Profile');
    const [user, setUser] = useState({
        name: null,
        email: null,
        company: 'Marsbazaar.com',
        position: 'Developer',
        phone: null,
        avatar: null
    });

    // Form validation states
    const [errors, setErrors] = useState({
        name: '',
        email: '',
        phone: ''
    });

    // Refs
    const fileInputRef = useRef(null);

    // Settings states
    const [industry, setIndustry] = useState('Pharmaceutical');
    const [industryDropdown, setIndustryDropdown] = useState(false);
    const industries = ['Pharmaceutical', 'Chemical', 'Automotive', 'Healthcare', 'Technology'];

    const [language, setLanguage] = useState('English');
    const [languageDropdown, setLanguageDropdown] = useState(false);
    const languages = ['English', 'Hindi', 'Gujarati', 'Spanish', 'French'];

    const [theme, setTheme] = useState('Light');
    const [themeDropdown, setThemeDropdown] = useState(false);
    const themes = ['Light', 'Dark'];

    // Toggle states
    const [emailNotifications, setEmailNotifications] = useState(true);
    const [pushNotifications, setPushNotifications] = useState(true);
    const [securityAlerts, setSecurityAlerts] = useState(true);

    // Danger zone states
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    // Validate form fields
    const validateField = (name, value) => {
        let error = '';
        console.log("name val",name,value);
        

        if (name === 'name' && !value.trim()) {
            error = 'Name is required';
        } else if (name === 'email') {
            if (!value.trim()) {
                error = 'Email is required';
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                error = 'Invalid email format';
            }
        } else if (name === 'phone') {
            const trimmed = value.trim();
            const phoneRegex = /^\+?[\d\s\-()]{10,20}$/;
            if (!phoneRegex.test(trimmed)) {
                error = 'Invalid phone number';
            }
        }

        setErrors(prev => ({ ...prev, [name]: error }));
        return !error;
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setUser(prev => ({ ...prev, [name]: value }));
        validateField(name, value);
    };

    const handleSaveChanges = async () => {
        if (!user || !currentUser) return;
    
        const isNameValid = validateField('name', user.name);
        const isPhoneValid = validateField('phone', user.phone);
    
        if (isNameValid && isPhoneValid) {
            try {
                let userImageURL = user.avatar; // fallback if image isn't changed
    
                if (user.avatarFile) {
                    const uploaded = await upload(user.avatarFile, 'Home');
                    userImageURL = uploaded?.file_url;
                }
    
                await updateDoc('User', currentUser, {
                    full_name: user.name,
                    mobile_no: user.phone,
                    user_image: userImageURL,
                });
    
                toast.success('Profile updated successfully!', {
                    position: "top-center",
                    autoClose: 3000,
                    theme: "colored",
                });
    
            } catch (err) {
                console.error('Error updating user:', err);
                toast.error('Something went wrong while saving.', {
                    position: "top-center",
                    autoClose: 3000,
                    theme: "colored",
                });
            }
        }
    };
    

    const handleDeleteAccount = () => {
        // Account deletion logic
        alert('Account deletion initiated');
        setShowDeleteConfirm(false);
    };

    const handlePhotoUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
    
            if (file.size > 2 * 1024 * 1024) {
                alert('Image size should be less than 2MB');
                return;
            }
    
            const reader = new FileReader();
            reader.onload = (event) => {
                setUser(prev => ({
                    ...prev,
                    avatar: event.target.result,   // for image preview (base64)
                    avatarFile: file              // store original File for Frappe upload
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    const removePhoto = () => {
        setUser(prev => ({ ...prev, avatar: null }));
    };

    const triggerFileInput = () => {
        fileInputRef.current.click();
    };

    useEffect(() => {
        if (userDoc) {
          console.log("Fetched user document:", userDoc);
          setUser({
            name: userDoc.first_name,
            email: userDoc.email,
            company: 'Pharmaceutical Pvt Ltd.',
            position: "Senior Manager",
            phone:  userDoc.mobile_no || null,
            avatar: userDoc.user_image || null
        })
        }
      }, [userDoc]);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl h-[85vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-[#0e2044] text-white p-4 flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                        <IoSettingsOutline className="text-xl" />
                        <h2 className="text-xl font-bold">Account Settings</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-full hover:bg-white hover:bg-opacity-20 transition"
                    >
                        <IoClose className="text-xl" />
                    </button>
                </div>

                <div className="flex flex-1 overflow-hidden">
                    {/* Sidebar */}
                    <div className="w-56 bg-gray-50 border-r flex flex-col">
                        <div className="p-4 border-b">
                            <div className="flex items-center space-x-3">
                                {user.avatar ? (
                                    <img
                                        src={user.avatar}
                                        alt="User"
                                        className="w-10 h-10 rounded-full object-cover relative"
                                    />
                                ) : (
                                    <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                                        <CiUser className="text-gray-600 text-xl" />
                                    </div>
                                )}
                                <div>
                                    <p className="font-medium">{user.name}</p>
                                    <p className="text-xs text-gray-500">{user.email}</p>
                                </div>
                            </div>
                        </div>

                        <nav className="flex-1 overflow-y-auto p-2">
                            <button
                                onClick={() => setActiveTab('Profile')}
                                className={`w-full flex items-center space-x-2 p-3 rounded-lg text-left transition ${activeTab === 'Profile' ? 'bg-[#41b655] text-white' : 'hover:bg-gray-100'}`}
                            >
                                <IoMdPerson />
                                <span>Profile</span>
                            </button>

                            <button
                                onClick={() => setActiveTab('Security')}
                                className={`w-full flex items-center space-x-2 p-3 rounded-lg text-left transition ${activeTab === 'Security' ? 'bg-[#41b655] text-white' : 'hover:bg-gray-100'}`}
                            >
                                <IoMdLock />
                                <span>Security</span>
                            </button>

                            <button
                                onClick={() => setActiveTab('Notifications')}
                                className={`w-full flex items-center space-x-2 p-3 rounded-lg text-left transition ${activeTab === 'Notifications' ? 'bg-[#41b655] text-white' : 'hover:bg-gray-100'}`}
                            >
                                <IoMdNotificationsOutline />
                                <span>Notifications</span>
                            </button>

                            <button
                                onClick={() => setActiveTab('Preferences')}
                                className={`w-full flex items-center space-x-2 p-3 rounded-lg text-left transition ${activeTab === 'Preferences' ? 'bg-[#41b655] text-white' : 'hover:bg-gray-100'}`}
                            >
                                <IoMdColorPalette />
                                <span>Preferences</span>
                            </button>

                            <button
                                onClick={() => setActiveTab('DangerZone')}
                                className={`w-full flex items-center space-x-2 p-3 rounded-lg text-left transition ${activeTab === 'DangerZone' ? 'bg-red-100 text-red-600' : 'hover:bg-gray-100'}`}
                            >
                                <IoMdInformationCircle />
                                <span>Danger Zone</span>
                            </button>
                        </nav>

                        <div className="p-4 border-t">
                            <button className="w-full flex items-center justify-center space-x-2 p-2 text-red-600 rounded-lg hover:bg-red-50 transition">
                                <IoMdLogOut />
                                <span>Log Out</span>
                            </button>
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {/* Profile Tab */}
                        {activeTab === 'Profile' && (
                            <div className="space-y-6 h-full flex flex-col">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-semibold">Personal Information</h3>
                                    <button
                                        onClick={handleSaveChanges}
                                        className="px-4 py-2 bg-[#41b655] text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50"
                                        disabled={Object.values(errors).some(error => error)}
                                    >
                                        Save Changes
                                    </button>
                                </div>

                                <div className="flex flex-col md:flex-row gap-6 flex-1 overflow-auto">
                                    <div className="flex flex-col items-center space-y-3">
                                        {user.avatar ? (
                                            <img
                                                src={user.avatar}
                                                alt="User"
                                                className="w-24 h-24 rounded-full object-cover border-4 border-gray-200 relative"
                                            />
                                        ) : (
                                            <div className="w-24 h-24 rounded-full bg-gray-200 border-4 border-gray-200 flex items-center justify-center">
                                                <CiUser className="text-gray-600 text-4xl" />
                                            </div>
                                        )}
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            onChange={handlePhotoUpload}
                                            accept="image/*"
                                            className="hidden"
                                        />
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={triggerFileInput}
                                                className="text-sm px-3 py-1 bg-[#41b655] text-white rounded-lg hover:bg-green-600 transition"
                                            >
                                                {user.avatar ? 'Change' : 'Upload'}
                                            </button>
                                            {user.avatar && (
                                                <button
                                                    onClick={removePhoto}
                                                    className="text-sm px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
                                                >
                                                    Remove
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Personal Information Group */}
                                        <div className="space-y-4">
                                            <h4 className="font-medium text-gray-700 border-b pb-2">Personal Details</h4>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name*</label>
                                                <input
                                                    type="text"
                                                    name="name"
                                                    value={user.name}
                                                    onChange={handleInputChange}
                                                    onBlur={(e) => validateField('name', e.target.value)}
                                                    className={`w-full px-3 py-2 border ${errors.name ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent`}
                                                />
                                                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Email*</label>
                                                <input readOnly
                                                    type="email"
                                                    name="email"
                                                    value={user.email}
                                                    onChange={handleInputChange}
                                                    onBlur={(e) => validateField('email', e.target.value)}
                                                    className={`w-full px-3 py-2 border ${errors.email ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent`}
                                                />
                                                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                                                <input
                                                    type="tel"
                                                    name="phone"
                                                    value={user.phone}
                                                    onChange={handleInputChange}
                                                    onBlur={(e) => validateField('phone', e.target.value)}
                                                    className={`w-full px-3 py-2 border ${errors.phone ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent`}
                                                />
                                                {errors.phone && <p className="text-red-500 text-xs mt-1">{errors.phone}</p>}
                                            </div>
                                        </div>

                                        {/* Professional Information Group */}
                                        <div className="space-y-4">
                                            <h4 className="font-medium text-gray-700 border-b pb-2">Professional Details</h4>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                                                <input
                                                    type="text"
                                                    name="company"
                                                    value={user.company}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent"
                                                />
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                                                <input
                                                    type="text"
                                                    name="position"
                                                    value={user.position}
                                                    onChange={handleInputChange}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent"
                                                />
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
                                                <div className="relative">
                                                    <button
                                                        onClick={() => setIndustryDropdown(!industryDropdown)}
                                                        className="w-full flex justify-between items-center px-3 py-2 border border-gray-300 rounded-lg bg-white"
                                                    >
                                                        <span>{industry}</span>
                                                        {industryDropdown ? <IoMdArrowDropup /> : <IoMdArrowDropdown />}
                                                    </button>
                                                    {industryDropdown && (
                                                        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
                                                            {industries.map((item) => (
                                                                <button
                                                                    key={item}
                                                                    onClick={() => {
                                                                        setIndustry(item);
                                                                        setIndustryDropdown(false);
                                                                    }}
                                                                    className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${industry === item ? 'bg-[#41b655] text-white hover:bg-[#41b655]' : ''}`}
                                                                >
                                                                    {item}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Security Tab */}
                        {activeTab === 'Security' && (
                            <div className="space-y-6 h-full flex flex-col">
                                <h3 className="text-lg font-semibold">Security Settings</h3>

                                <div className="space-y-4 flex-1 overflow-auto">
                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Password</h4>
                                                <p className="text-sm text-gray-500">Last changed 3 months ago</p>
                                            </div>
                                            <button className="text-[#41b655] hover:underline">Change Password</button>
                                        </div>
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Login Activity</h4>
                                                <p className="text-sm text-gray-500">View your recent login history</p>
                                            </div>
                                            <button className="text-[#41b655] hover:underline">View Activity</button>
                                        </div>
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Session Management</h4>
                                                <p className="text-sm text-gray-500">Manage active sessions</p>
                                            </div>
                                            <button className="text-[#41b655] hover:underline">Manage Sessions</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Notifications Tab */}
                        {activeTab === 'Notifications' && (
                            <div className="space-y-6 h-full flex flex-col">
                                <h3 className="text-lg font-semibold">Notification Preferences</h3>

                                <div className="space-y-4 flex-1 overflow-auto">
                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Email Notifications</h4>
                                                <p className="text-sm text-gray-500">Receive notifications via email</p>
                                            </div>
                                            <div
                                                onClick={() => setEmailNotifications(!emailNotifications)}
                                                className={`w-12 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${emailNotifications ? 'bg-[#41b655]' : 'bg-gray-300'}`}
                                            >
                                                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${emailNotifications ? 'translate-x-6' : ''}`}></div>
                                            </div>
                                        </div>

                                        {emailNotifications && (
                                            <div className="mt-3 space-y-3">
                                                <div className="flex justify-between items-center">
                                                    <div>
                                                        <p className="text-sm">Product Updates</p>
                                                        <p className="text-xs text-gray-500">News about new features and improvements</p>
                                                    </div>
                                                    <input type="checkbox" defaultChecked className="h-4 w-4 text-[#41b655] rounded" />
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <div>
                                                        <p className="text-sm">Security Alerts</p>
                                                        <p className="text-xs text-gray-500">Important notifications about your account security</p>
                                                    </div>
                                                    <input type="checkbox" defaultChecked className="h-4 w-4 text-[#41b655] rounded" />
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <div>
                                                        <p className="text-sm">Marketing Communications</p>
                                                        <p className="text-xs text-gray-500">News and offers (you can unsubscribe anytime)</p>
                                                    </div>
                                                    <input type="checkbox" className="h-4 w-4 text-[#41b655] rounded" />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Push Notifications</h4>
                                                <p className="text-sm text-gray-500">Receive notifications on your device</p>
                                            </div>
                                            <div
                                                onClick={() => setPushNotifications(!pushNotifications)}
                                                className={`w-12 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${pushNotifications ? 'bg-[#41b655]' : 'bg-gray-300'}`}
                                            >
                                                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${pushNotifications ? 'translate-x-6' : ''}`}></div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Security Alerts</h4>
                                                <p className="text-sm text-gray-500">Get notified about important security events</p>
                                            </div>
                                            <div
                                                onClick={() => setSecurityAlerts(!securityAlerts)}
                                                className={`w-12 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${securityAlerts ? 'bg-[#41b655]' : 'bg-gray-300'}`}
                                            >
                                                <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${securityAlerts ? 'translate-x-6' : ''}`}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Preferences Tab */}
                        {activeTab === 'Preferences' && (
                            <div className="space-y-6 h-full flex flex-col">
                                <h3 className="text-lg font-semibold">App Preferences</h3>

                                <div className="space-y-4 flex-1 overflow-auto">
                                    <div className="p-4 border rounded-lg">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
                                        <div className="relative">
                                            <button
                                                onClick={() => setLanguageDropdown(!languageDropdown)}
                                                className="w-full flex justify-between items-center px-3 py-2 border border-gray-300 rounded-lg bg-white"
                                            >
                                                <span>{language}</span>
                                                {languageDropdown ? <IoMdArrowDropup /> : <IoMdArrowDropdown />}
                                            </button>
                                            {languageDropdown && (
                                                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
                                                    {languages.map((item) => (
                                                        <button
                                                            key={item}
                                                            onClick={() => {
                                                                setLanguage(item);
                                                                setLanguageDropdown(false);
                                                            }}
                                                            className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${language === item ? 'bg-[#41b655] text-white hover:bg-[#41b655]' : ''}`}
                                                        >
                                                            {item}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
                                        <div className="relative">
                                            <button
                                                onClick={() => setThemeDropdown(!themeDropdown)}
                                                className="w-full flex justify-between items-center px-3 py-2 border border-gray-300 rounded-lg bg-white"
                                            >
                                                <span>{theme}</span>
                                                {themeDropdown ? <IoMdArrowDropup /> : <IoMdArrowDropdown />}
                                            </button>
                                            {themeDropdown && (
                                                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
                                                    {themes.map((item) => (
                                                        <button
                                                            key={item}
                                                            onClick={() => {
                                                                setTheme(item);
                                                                setThemeDropdown(false);
                                                            }}
                                                            className={`w-full text-left px-3 py-2 hover:bg-gray-100 ${theme === item ? 'bg-[#41b655] text-white hover:bg-[#41b655]' : ''}`}
                                                        >
                                                            {item}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="p-4 border rounded-lg">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Time Zone</label>
                                        <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#41b655] focus:border-transparent">
                                            <option>(UTC-05:00) Eastern Time (US & Canada)</option>
                                            <option>(UTC-08:00) Pacific Time (US & Canada)</option>
                                            <option>(UTC+00:00) London</option>
                                            <option>(UTC+05:30) India</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Danger Zone Tab */}
                        {activeTab === 'DangerZone' && (
                            <div className="space-y-6 h-full flex flex-col">
                                <h3 className="text-lg font-semibold text-red-600">Danger Zone</h3>

                                <div className="space-y-4 flex-1 overflow-auto">
                                    <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium text-red-700">Delete Account</h4>
                                                <p className="text-sm text-red-600">Permanently delete your account and all data</p>
                                            </div>
                                            <button
                                                onClick={() => setShowDeleteConfirm(true)}
                                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                                            >
                                                Delete
                                            </button>
                                        </div>

                                        {showDeleteConfirm && (
                                            <div className="mt-4 p-4 bg-white border border-red-300 rounded-lg">
                                                <h5 className="font-medium mb-2">Are you absolutely sure?</h5>
                                                <p className="text-sm text-gray-600 mb-4">
                                                    This action cannot be undone. This will permanently delete your account and remove all data associated with it.
                                                </p>
                                                <div className="flex justify-end space-x-3">
                                                    <button
                                                        onClick={() => setShowDeleteConfirm(false)}
                                                        className="px-3 py-1 border rounded-lg hover:bg-gray-50"
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button
                                                        onClick={handleDeleteAccount}
                                                        className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700"
                                                    >
                                                        Confirm Deletion
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-4 border border-yellow-200 rounded-lg bg-yellow-50">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium text-yellow-700">Export Data</h4>
                                                <p className="text-sm text-yellow-600">Download all your data in a ZIP file</p>
                                            </div>
                                            <button className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition">
                                                Export
                                            </button>
                                        </div>
                                    </div>

                                    <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <h4 className="font-medium">Deactivate Account</h4>
                                                <p className="text-sm text-gray-600">Temporarily disable your account</p>
                                            </div>
                                            <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition">
                                                Deactivate
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <ToastContainer />
        </div>
    );
}

export default Settings
