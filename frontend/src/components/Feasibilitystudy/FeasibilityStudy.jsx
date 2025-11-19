import React, { useState, useContext, useEffect } from 'react';
import { FrappeContext, useFrappeAuth, useFrappeEventListener } from 'frappe-react-sdk';
import { FaFilePdf, FaRegLightbulb, FaIndustry, FaAward } from 'react-icons/fa';
import { FiUploadCloud, FiCheckCircle, FiAlertCircle, FiX, FiMapPin, FiPackage, FiShoppingCart, FiTool, FiUsers, FiHome, FiDollarSign, FiInfo } from 'react-icons/fi';
import { useDispatch } from 'react-redux';
import { addInputtext } from '../../Redux/Store/Featuresilces/chat';
import 'react-toastify/dist/ReactToastify.css';
import ProcessFlowAnimation from '../Processflowanimation/ProcessFlowAnimation';
import { addFeasibilityId } from '../../Redux/Store/Featuresilces/Feasibility';

const FeasibilityStudy = ({ isOpen, onClose,setHasUnseenReport, resultJson}) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'processing', 'done', 'error'
    const [resultData, setResultData] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [pendingReport, setPendingReport] = useState(null);
    const [processingRecord, setProcessingRecord] = useState(null);
    const [showHowItWorks, setShowHowItWorks] = useState(true);
    const dispatch = useDispatch();

    const { call } = useContext(FrappeContext);
    const { currentUser } = useFrappeAuth();

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setSelectedFile(file);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            setSelectedFile(file);
        }
    };

    const removeFile = () => {
        setSelectedFile(null);
    };

    const resetUploadState = () => {
        setStatus('idle');
        setSelectedFile(null);
        setUploadProgress(0);
        setResultData(null);
        setErrorMessage('');
        setPendingReport(null);
        setProcessingRecord(null);
    };

    const validateResultData = (data) => {
        if (!data || typeof data !== 'object') {
            return { isValid: false, error: 'Invalid result data structure' };
        }

        // Check if required top-level keys exist
        const requiredKeys = ['structured_summary', 'classified_queries', 'summary_display_statement'];
        const missingKeys = requiredKeys.filter(key => !(key in data));

        if (missingKeys.length > 0) {
            console.warn('Missing keys in result data:', missingKeys);
            // Optionally, return invalid if critical keys are missing
            return { isValid: false, error: `Missing required keys: ${missingKeys.join(', ')}` };
        }

        // Check for irrelevance
        if (data.relevance === 'irrelevant document') {
            return { isValid: false, error: data?.user_friendly_error_message || 'Document marked as irrelevant' };
        }

        // Check for null classified queries
        if (data.classified_queries === null) {
            return { isValid: false, error: 'Classified queries are null' };
        }

        return { isValid: true, error: null };
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setStatus('uploading');
        setUploadProgress(0);
        setIsUploading(true);
        setErrorMessage('');
        setResultData(null);

        const MIN_UPLOAD_TIME = 5000; // 5 seconds minimum
        const uploadStartTime = Date.now();

        try {
            // Simulate upload progress
            const intervalDuration = 10;
            let currentProgress = 0;
            const progressInterval = setInterval(() => {
                if (currentProgress < 99) {
                    currentProgress += 1;
                    setUploadProgress(currentProgress);
                }
            }, intervalDuration);

            // 1. Create FormData for file upload
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('is_private', 0);
            formData.append('doctype', '');
            formData.append('docname', '');

            // 2. Upload file
            const response = await fetch('/api/method/upload_file', {
                method: 'POST',
                body: formData,
            });

            const elapsed = Date.now() - uploadStartTime;
            if (elapsed < MIN_UPLOAD_TIME) {
                await new Promise(res => setTimeout(res, MIN_UPLOAD_TIME - elapsed));
            }
            clearInterval(progressInterval);

            const result = await response.json();

            if (!result.message || !result.message.file_url) {
                throw new Error('File upload failed');
            }

            setUploadProgress(100);
            const fileUrl = result.message.file_url;
            // console.log("✅ File uploaded at:", fileUrl);

            // 3. Process file
            setStatus('processing');
            const analysisResult = await call.get(
                "frontend_app.Management_Class.Ai_management.feasibility.feasibility_method_call",
                { file_path: fileUrl }
            );

            // console.log("📊 AI Feasibility Result:", analysisResult.message);

        } catch (err) {
            console.error("❌ Upload/Analysis Error:", err);
            setStatus('error');
            setErrorMessage(err.message || 'An error occurred during processing. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    useEffect(() => {
        // console.log("fesibility json", resultJson);
        let isValidJsonWithData = false;

        try {
            const parsed = JSON.parse(resultJson);
            isValidJsonWithData = parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0;
        } catch (e) {
            isValidJsonWithData = false;
        }

        if (isValidJsonWithData) {
            try {
                const results = JSON.parse(resultJson)
                const validation = validateResultData(results);
                if (!validation.isValid) {
                    throw new Error(validation.error);
                }
                setResultData(results)
            setStatus('success');

            } catch (err) {
                setErrorMessage(err.message || "Failed to fetch or process result");
                setStatus("error");
            }

            
        }
        else {
            // Check for existing records when component mounts
            checkExistingRecords();
        }

    }, []);

    useEffect(() => {
        if(!resultJson){
            checkExistingRecords();
        }
    }, [currentUser,resultJson])

    // Check for existing processing records and unseen reports
    const checkExistingRecords = async () => {
        try {
            setStatus('loading');

            // Check for processing records
            const processingCheck = await call.get("frappe.client.get_list", {
                doctype: "Feasibility Report",
                filters: {
                    owner: ["=", currentUser],
                    status: ["in", ["Processing", "Uploading", "Analyzing"]]
                },
                fields: ["name", "status", "creation", "file_path"],
                order_by: "creation desc",
                limit_page_length: 1
            });
            // console.log("processing record", processingCheck);

            if (processingCheck.message && processingCheck.message.length > 0) {
                setProcessingRecord(processingCheck.message[0]);
                setStatus('processing');
                return;
            }

            // Check for unseen completed reports
            const unseenCheck = await call.get("frappe.client.get_list", {
                doctype: "Feasibility Report",
                filters: {
                    owner: ["=", currentUser],
                    status: ["in", ["Complete", "Fail"]],
                    seen_by_user: ["=", 0]
                },
                fields: ["name","feasibility_title", "result_data", "creation", "file_path"],
                order_by: "creation desc",
                limit_page_length: 1
            });
            // console.log("unchecked records", unseenCheck);
            
            if (unseenCheck.message && unseenCheck.message.length > 0) {
                const unseenReport = unseenCheck.message[0];
                try {
                    const parsedResult = JSON.parse(unseenReport.result_data);
                    setPendingReport(unseenReport);
                    setResultData(parsedResult);
                    setStatus('pending_report');
                    // Set hasUnseenReport to true for navbar indicator
                    setHasUnseenReport(true);
                } catch (parseError) {
                    // console.error("Error parsing unseen report:", parseError);
                    setStatus('idle');
                }
                return;
            }

            // No processing records or unseen reports
            setStatus('idle');
            setHasUnseenReport(false);

        } catch (error) {
            // console.error("Error checking existing records:", error);
            setStatus('idle');
        }
    };

    // Mark report as seen
    const markReportAsSeen = async (reportName) => {
        try {
            await call.post("frappe.client.set_value", {
                doctype: "Feasibility Report",
                name: reportName,
                fieldname: "seen_by_user",
                value: 1
            });
            // Update hasUnseenReport state
            setHasUnseenReport(false);
        } catch (error) {
            // console.error("Error marking report as seen:", error);
        }
    };  

    const handleViewPendingReport = async () => {
        
        if (pendingReport) {
            const pendingResultData = pendingReport?.result_data
            if(JSON.parse(pendingResultData)?.classified_queries){
                setStatus('success');
            }
            else{
                console.log(pendingResultData,'okay');
                
                setStatus('error');
            }
            await markReportAsSeen(pendingReport.name);
            
            setPendingReport(null);
        }
        else{
            setStatus("error")
        }
    };

    const handleDismissPendingReport = async () => {
        if (pendingReport) {
            await markReportAsSeen(pendingReport.name);
            setPendingReport(null);
            setResultData(null);
            setStatus('idle');
        }
    };

    const handleQuerySelect = (query) => {
        // console.log('This is the query', query)
        if (query) {
            dispatch(addInputtext(query))
            onClose();
            resetUploadState();
        }
    }

    const [feasibilityId, setFeasibilityId] = useState()
    useFrappeEventListener("feasibility_analysis_done", async (data) => {
        
        if (data.status === "done" && data.docname) {
            try {
                // Fetch the Feasibility Report using the provided docname
                const res = await call.get("frappe.client.get", {
                    doctype: "Feasibility Report",
                    name: data.docname,
                });

                // Check if res.message exists and has result_data
                if (!res.message || !res.message.result_data) {
                    throw new Error("No result data found in the report");
                }

                let parsedResult;
                try {
                    parsedResult = JSON.parse(res.message.result_data);
                } catch (parseError) {
                    // console.error("❌ JSON Parse Error:", parseError);
                    throw new Error("Failed to parse result data. Invalid JSON format.");
                }

                // Validate the parsed result
                const validation = validateResultData(parsedResult);
                if (!validation.isValid) {
                    throw new Error(validation.error);
                }

                dispatch(addFeasibilityId(data.docname))
                setResultData(parsedResult);
                setStatus("success");
                await markReportAsSeen(data.docname);

            } catch (err) {
                // console.error("❌ Error fetching result:", err);
                setErrorMessage(err.message || "Failed to fetch or process result");
                setStatus("error");
                await markReportAsSeen(data.docname);
            }
        } else {
            // console.error("❌ Invalid event data or processing failed:", data);
            setErrorMessage(data.message || "Processing failed");
            setStatus("error");
            await markReportAsSeen(data.docname);
        }
    });

    if (!isOpen) return null;

    return (
        <>
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className={`bg-white rounded-xl ${showHowItWorks ? 'w-[75%]' : 'w-[60%]'} h-[80%] flex flex-col overflow-hidden shadow-2xl`}>
                    {/* Modal Header */}
                    <div className="bg-[#0B2152] text-white p-5 flex justify-between items-center">
                        <div className="flex items-center space-x-3">
                            <FaRegLightbulb size={24} className="text-[#70A1D9]" />
                            <h3 className="text-xl font-semibold">Feasibility Study Analysis</h3>
                        </div>
                        <button
                            onClick={() => {
                                onClose();
                                resetUploadState();
                            }}
                            className="p-1 rounded-full hover:bg-[#2C53A3] transition-colors"
                        >
                            <FiX size={24} />
                        </button>
                    </div>

                    {/* Modal Body - Scrollable Content */}
                    <div className="flex-1 overflow-y-auto ">
                        {status === 'loading' && (
                            <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
                                <div className="relative mb-8">
                                    <div className="w-16 h-16 border-4 border-[#70A1D9] border-t-transparent rounded-full animate-spin"></div>
                                </div>
                                <h3 className="text-xl font-semibold text-[#0B2152] mb-3">Checking for existing reports...</h3>
                                <p className="text-gray-600 text-center max-w-md">
                                    Please wait while we check for any pending analysis or unseen reports.
                                </p>
                            </div>
                        )}

                        {/* Pending Report State */}
                        {status === 'pending_report' && pendingReport && (
                            <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
                                <div className="mb-6 p-4 bg-blue-100 rounded-full">
                                    <FiCheckCircle className="text-blue-600" size={54} />
                                </div>
                                <h3 className="text-2xl font-semibold text-[#0B2152] mb-2">Report Ready!</h3>
                                <p className="text-gray-600 text-center max-w-md mb-4">
                                    You have a completed feasibility analysis report that hasn't been viewed yet.
                                </p>

                                <div className="bg-[#F5F9FF] border border-[#70A1D9] rounded-xl p-4 mb-6 w-full max-w-md">
                                    <div className="text-center">
                                        <p className="text-sm text-[#2C53A3] mb-2">Report Generated:</p>
                                        <p className="font-medium text-[#0B2152]">
                                            {pendingReport.feasibility_title || pendingReport.name} at {new Date(pendingReport.creation).toLocaleTimeString()}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex space-x-4">
                                    <button
                                        onClick={handleViewPendingReport}
                                        className="px-8 py-2 bg-gradient-to-r from-[#2C53A3] to-[#0B2152] text-white rounded-lg hover:from-[#0B2152] hover:to-[#2C53A3] shadow-md transition-colors"
                                    >
                                        View Report
                                    </button>
                                    <button
                                        onClick={handleDismissPendingReport}
                                        className="px-6 py-2 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors border border-gray-300"
                                    >
                                        Start New Analysis
                                    </button>
                                </div>
                            </div>
                        )}

                        {status === 'idle' && (
                            <div className="flex flex-row-reverse gap-16 items-center justify-center w-full h-full">
                                {/* How It Works Section - Collapsible */}
                                {showHowItWorks && (
                                    <div className="w-[45%]  h-full flex items-center justify-center animate-fade-in">
                                        <div className='relative h-[76%] w-[85%] flex items-center justify-center'>
                                            <ProcessFlowAnimation />
                                        </div>
                                    </div>
                                )}

                                {/* File Upload Area - Enhanced */}
                                <div className={`h-[90%] ${showHowItWorks ? 'w-[50%]' : 'w-full'} flex flex-col items-center px-4`}>
                                    <div
                                        className={`border-2 border-dashed rounded-xl h-full flex items-center justify-center relative p-4 text-center transition-all w-full
                                        ${isDragging ? 'border-[#4CAF50] bg-[#f0f9f0]' : 'border-[#70A1D9]'} 
                                        ${selectedFile ? 'border-solid border-[#4CAF50] bg-[#f0f9f0]' : 'bg-white'}`}
                                        onDragOver={handleDragOver}
                                        onDragLeave={handleDragLeave}
                                        onDrop={handleDrop}
                                    >
                                        {!selectedFile ? (
                                            <div className="space-y-4">
                                                <div className="animate-bounce">
                                                    <FiUploadCloud className="mx-auto text-[#2C53A3]" size={48} />
                                                </div>
                                                <div className="space-y-2">
                                                    <p className="text-xl font-medium text-[#0B2152]">
                                                        {isDragging ? 'Drop your PDF here' : 'Drag & drop your PDF file here'}
                                                    </p>
                                                    <p className="text-gray-500 text-sm">or</p>
                                                </div>
                                                <label className="inline-block bg-gradient-to-r from-[#2C53A3] to-[#0B2152] hover:from-[#0B2152] hover:to-[#2C53A3] text-white px-6 py-2.5 rounded-lg cursor-pointer transition-all shadow-md hover:shadow-lg">
                                                    Browse Files
                                                    <input
                                                        type="file"
                                                        accept=".pdf"
                                                        className="hidden"
                                                        onChange={handleFileChange}
                                                    />
                                                </label>
                                                <p className="text-xs text-gray-500 mt-3">Supports PDF files</p>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center animate-fade-in">
                                                <div className="relative">
                                                    <FaFilePdf className="text-red-500" size={48} />
                                                    <div className="absolute -top-2 -right-2 bg-[#4CAF50] text-white rounded-full p-1">
                                                        <FiCheckCircle size={16} />
                                                    </div>
                                                </div>
                                                <div className="mt-5 text-center space-y-1">
                                                    <p className="font-medium text-[#0B2152] truncate max-w-xs">{selectedFile.name}</p>
                                                    <p className="text-sm text-gray-500">
                                                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                                                    </p>
                                                </div>
                                                <div className="mt-6 flex gap-4">
                                                    <button
                                                        onClick={removeFile}
                                                        className="px-4 py-2 text-[#E91E63] hover:text-[#c2185b] flex items-center border border-[#E91E63] rounded-lg hover:border-[#c2185b]"
                                                    >
                                                        <FiX className="mr-1" /> Remove
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Additional Info */}
                                    {!selectedFile && (
                                        <div className="mt-2 text-center max-w-2xl">
                                            <p className="text-gray-600 text-sm">
                                                Our AI will analyze your document and provide a comprehensive feasibility report within some minutes.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Uploading State */}
                        {status === 'uploading' && (
                            <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
                                <div className="relative mb-8">
                                    <div className="w-20 h-20 border-4 border-[#2C53A3] border-t-transparent rounded-full animate-spin"></div>
                                    <FiUploadCloud className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-[#2C53A3]" size={28} />
                                </div>
                                <h3 className="text-2xl font-semibold text-[#0B2152] mb-3">Uploading Your File</h3>
                                <p className="text-gray-600 mb-8 max-w-md text-center">Please wait while we upload your document...</p>

                                <div className="w-full max-w-md mb-8">
                                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                                        <span>Progress</span>
                                        <span>{uploadProgress}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                                        <div
                                            className="bg-gradient-to-r from-[#4CAF50] to-[#2C53A3] h-3 rounded-full transition-all duration-300"
                                            style={{ width: `${uploadProgress}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Processing State */}
                        {status === 'processing' && (
                            <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
                                <div className="relative mb-8">
                                    <div className="w-20 h-20 border-4 border-[#4CAF50] border-b-transparent rounded-full animate-spin"></div>
                                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                                        <div className="animate-pulse">
                                            <FaRegLightbulb className="text-[#4CAF50]" size={28} />
                                        </div>
                                    </div>
                                </div>
                                <h3 className="text-2xl font-semibold text-[#0B2152] mb-3">
                                    {processingRecord ? 'Analysis in Progress' : 'Analyzing Document'}
                                </h3>
                                <p className="text-gray-600 text-center max-w-md mb-6">
                                    {processingRecord
                                        ? 'Your document is currently being analyzed. This process was started earlier and is still in progress.'
                                        : 'Our AI is carefully analyzing your document to extract key feasibility metrics.'
                                    }
                                </p>

                                {processingRecord && (
                                    <div className="bg-[#F5F9FF] border border-[#70A1D9] rounded-xl p-4 mb-6 w-full max-w-md">
                                        <div className="text-center">
                                            <p className="text-sm text-[#2C53A3] mb-1">Started:</p>
                                            <p className="font-medium text-[#0B2152] text-sm">
                                                {new Date(processingRecord.creation).toLocaleDateString()} at {new Date(processingRecord.creation).toLocaleTimeString()}
                                            </p>
                                        </div>
                                    </div>
                                )}
                                <div className="bg-[#F5F9FF] border border-[#70A1D9] text-[#0B2152] p-4 rounded-lg max-w-md animate-pulse">
                                    <div className="flex items-center">
                                        <FiAlertCircle className="text-[#2C53A3] mr-2" />
                                        <p>Processing may take 1-2 minutes. You can safely leave this page.</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Success State */}
                        {status === 'success' && resultData && (
                            <div className="flex flex-col">
                                {/* Main Content Container */}
                                <div className="space-y-6 pb-4">
                                    {/* Summary Card */}
                                    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-[#70A1D9]/20">
                                        <div className="bg-gradient-to-r from-[#0B2152] to-[#2C53A3] px-6 py-4">
                                            <h4 className="text-white font-semibold text-lg flex items-center">
                                                <FiPackage className="mr-2" /> Project Summary
                                            </h4>
                                        </div>
                                        <div className="p-6">
                                            {resultData?.summary_display_statement && (
                                                <p className="text-gray-700 mb-6">
                                                    {resultData.summary_display_statement}
                                                </p>
                                            )}

                                            {resultData?.structured_summary && (
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                                                    {/* Product Info */}
                                                    <div className="bg-[#F5F9FF] p-5 rounded-lg border border-[#70A1D9]/30">
                                                        <h5 className="font-medium text-[#0B2152] mb-3 flex items-center">
                                                            <FaIndustry className="mr-2 text-[#2C53A3]" /> Product Details
                                                        </h5>
                                                        <div className="space-y-3">
                                                            {resultData.structured_summary.product && (
                                                                <div>
                                                                    <span className="text-sm font-medium text-[#2C53A3]">Product:</span>
                                                                    <p className="text-[#0B2152] font-medium mt-1">
                                                                        {resultData.structured_summary.product}
                                                                        {resultData.structured_summary.final_product_capacity && (
                                                                            <span className="ml-2">
                                                                                {/* ({resultData.structured_summary.product_capacity}{resultData.structured_summary.product_unit}) */}
                                                                                {`(${resultData.structured_summary.final_product_capacity})`}
                                                                            </span>
                                                                        )}
                                                                    </p>
                                                                </div>
                                                            )}
                                                            {resultData.structured_summary.Location && (
                                                                <div>
                                                                    <span className="text-sm font-medium text-[#2C53A3]">Location:</span>
                                                                    <p className="text-[#0B2152] font-medium mt-1 flex items-center">
                                                                        <FiMapPin className="mr-1" /> {resultData.structured_summary.Location}
                                                                    </p>
                                                                </div>
                                                            )}
                                                            {(resultData.structured_summary.time_period || resultData.structured_summary.time_unit) && (
                                                                <div>
                                                                    <span className="text-sm font-medium text-[#2C53A3]">Timeline:</span>
                                                                    <p className="text-[#0B2152] font-medium mt-1 flex items-center">
                                                                        <FiCalendar className="mr-1" />
                                                                        {resultData.structured_summary.time_period} {resultData.structured_summary.time_unit}
                                                                    </p>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Supplies */}
                                                    {Array.isArray(resultData.structured_summary.supplies) && resultData.structured_summary.supplies.length > 0 && (
                                                        <div className="bg-[#F5F9FF] p-5 rounded-lg border border-[#70A1D9]/30">
                                                            <h5 className="font-medium text-[#0B2152] mb-3 flex items-center">
                                                                <FiShoppingCart className="mr-2 text-[#2C53A3]" /> Required Supplies
                                                            </h5>
                                                            <ul className="space-y-2">
                                                                {resultData.structured_summary.supplies.map((supply, index) => (
                                                                    <li key={index} className="flex items-center">
                                                                        <span className="w-2 h-2 bg-[#70A1D9] rounded-full mr-3"></span>
                                                                        <span className="text-[#0B2152]">{supply}</span>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}

                                                    {/* Equipments */}
                                                    {Array.isArray(resultData.structured_summary.equipments) && resultData.structured_summary.equipments.length > 0 && (
                                                        <div className="md:col-span-2 bg-[#F5F9FF] p-5 rounded-lg border border-[#70A1D9]/30">
                                                            <h5 className="font-medium text-[#0B2152] mb-3 flex items-center">
                                                                <FiTool className="mr-2 text-[#2C53A3]" /> Required Equipment
                                                            </h5>
                                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                                {resultData.structured_summary.equipments.map((equipment, index) => (
                                                                    <div key={index} className="flex items-center bg-white p-3 rounded-lg border border-[#70A1D9]/30 shadow-sm">
                                                                        <span className="w-2 h-2 bg-[#E91E63] rounded-full mr-3"></span>
                                                                        <span className="text-[#0B2152]">{equipment}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                </div>
                                            )}

                                            {/* User-Compatible Summary */}
                                            {resultData?.user_comaptible_structured_summary && (
                                                <div className="mt-6 bg-[#F5F9FF] p-5 rounded-lg border border-[#70A1D9]/30">
                                                    <h5 className="font-medium text-[#0B2152] mb-3 flex items-center">
                                                        <FiInfo className="mr-2 text-[#2C53A3]" /> Project Overview
                                                    </h5>
                                                    <p className="text-[#0B2152]">
                                                        {resultData.user_comaptible_structured_summary}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Follow-up Queries */}
                                    {Array.isArray(resultData?.classified_queries) && resultData.classified_queries.length > 0 && (
                                        <div className="bg-white rounded-xl shadow-md overflow-hidden border border-[#70A1D9]/20">
                                            <div className="bg-gradient-to-r from-[#0B2152] to-[#2C53A3] px-6 py-4">
                                                <h4 className="text-white font-semibold text-lg">Recommended Queries</h4>
                                            </div>
                                            <div className="p-6">
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {resultData.classified_queries.map((queryItem, index) => {
                                                        const iconMap = {
                                                            'Approval': <FiDollarSign className="text-[#673AB7]" />,
                                                            'Vendor Search': <FiShoppingCart className="text-[#E91E63]" />,
                                                            'Employment': <FiUsers className="text-[#4CAF50]" />,
                                                            'Build from Scratch': <FiHome className="text-[#2C53A3]" />,
                                                            'Incentives': <FaAward className="text-[#FF9800]" />
                                                        };

                                                        const bgMap = {
                                                            'Approval': 'bg-[#673AB7]/10',
                                                            'Vendor Search': 'bg-[#E91E63]/10',
                                                            'Employment': 'bg-[#4CAF50]/10',
                                                            'Build from Scratch': 'bg-[#2C53A3]/10',
                                                            'Incentives': 'bg-[#FF9800]/10'
                                                        };

                                                        return (
                                                            <button
                                                                key={index}
                                                                className={`text-left p-5 rounded-lg border border-gray-200 hover:border-[#2C53A3] hover:shadow-md transition-all duration-200 ${bgMap[queryItem.module] || 'bg-white'}`}
                                                                onClick={() => handleQuerySelect(queryItem.query)}
                                                            >
                                                                <div className="flex items-start">
                                                                    <div className={`p-2 rounded-full ${bgMap[queryItem.module]?.replace('/10', '/20') || 'bg-gray-100'} mr-4`}>
                                                                        {iconMap[queryItem.module] || <FiTool className="text-[#0B2152]" />}
                                                                    </div>
                                                                    <div>
                                                                        <p className="font-medium text-[#0B2152] text-left">{queryItem.query}</p>
                                                                        <p className="text-xs text-[#2C53A3] mt-2 font-medium">
                                                                            {queryItem.module}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                </div>
                            </div>
                        )}

                        {/* Error State */}
                        {status === 'error' && (
                            <div className="flex flex-col items-center justify-center h-full py-8 animate-fade-in">
                                <div className="mb-6 p-5 bg-red-100 rounded-full">
                                    <FiAlertCircle className="text-red-500" size={48} />
                                </div>
                                <h3 className="text-2xl font-semibold text-[#D32F2F] mb-3">Processing Error</h3>
                                <p className="text-gray-600 mb-8 text-center max-w-md">
                                    {errorMessage}
                                </p>

                                <div className="bg-red-50 border border-red-200 rounded-xl p-5 mb-8 w-full max-w-md">
                                    <div className="flex items-start">
                                        <FiAlertCircle className="text-red-500 mt-1 mr-3 flex-shrink-0" size={20} />
                                        <div>
                                            <h4 className="font-medium text-red-800 mb-2">Troubleshooting Tips</h4>
                                            <ul className="list-disc pl-5 text-red-700 text-sm space-y-1">
                                                <li>Ensure your PDF is not password protected</li>
                                                <li>Try again with a different document</li>
                                                <li>Contact support if the issue persists</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Modal Footer */}
                    <div className="bg-gray-50 px-6 py-2 border-t border-gray-200 flex justify-between items-center">
                        <div className="text-sm text-gray-500">
                            {status === 'idle' && !selectedFile && (
                                <span>Ready to upload your document</span>
                            )}
                            {status === 'idle' && selectedFile && (
                                <span className="flex items-center">
                                    <FaFilePdf className="text-red-500 mr-2" />
                                    {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)}MB)
                                </span>
                            )}
                            {status === 'success' && (
                                <span className="text-[#4CAF50] flex items-center">
                                    <FiCheckCircle className="mr-2" /> Analysis completed successfully
                                </span>
                            )}
                            {status === 'error' && (
                                <span className="text-red-500 flex items-center">
                                    <FiAlertCircle className="mr-2" /> Processing error occurred
                                </span>
                            )}
                        </div>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => {
                                    onClose();
                                    resetUploadState();
                                }}
                                className="px-6 py-1 text-md text-gray-700 rounded-lg hover:bg-gray-200 transition-colors border border-gray-300"
                            >
                                {status === 'success' ? 'Close' : 'Cancel'}
                            </button>
                            {status === 'idle' && (
                                <button
                                    onClick={handleUpload}
                                    disabled={!selectedFile || isUploading}
                                    className={`px-8 py-1 text-md rounded-lg text-white transition-colors 
                                        ${(!selectedFile || isUploading) ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-[#2C53A3] to-[#0B2152] hover:from-[#0B2152] hover:to-[#2C53A3] shadow-md'}`}
                                >
                                    Analyze Document
                                </button>
                            )}
                            {status === 'error' && (
                                <button
                                    onClick={resetUploadState}
                                    className="px-8 py-1 text-md rounded-lg bg-gradient-to-r from-[#E91E63] to-[#C2185B] text-white hover:from-[#C2185B] hover:to-[#E91E63] shadow-md transition-colors"
                                >
                                    Try Again
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default FeasibilityStudy;