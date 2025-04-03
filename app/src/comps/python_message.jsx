import React, { useState, useEffect } from 'react';
import { FaRegCopy,FaCheck } from "react-icons/fa";

const PythonMessage = ({ code, isRunning }) => {
  const [copied, setCopied] = useState(false);
  
  // Reset the copied state after 2 seconds
  useEffect(() => {
    let timeout;
    if (copied) {
      timeout = setTimeout(() => {
        setCopied(false);
      }, 2000);
    }
    return () => clearTimeout(timeout);
  }, [copied]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
    });
  };

  return (
    <div className="relative rounded-lg w-full bg-gray-800 p-4">
      {/* Code header with language indicator and copy button */}
      <div className="flex justify-between items-center mb-2 text-gray-300 text-sm">
        <span>Python</span>
        <button 
          onClick={copyToClipboard}
          className="flex items-center space-x-1 hover:text-white transition-colors"
        >
          {copied ? (
            <FaCheck className="h-4 w-4 text-green-500" />
          ) : (
            <FaRegCopy className="h-4 w-4" />
          )}
          <span>{copied ? 'Copied!' : 'Copy code'}</span>
        </button>
      </div>
      
      {/* Code content */}
      <pre className="text-gray-100 overflow-x-auto p-2 font-mono text-sm">
        <code>{code}</code>
      </pre>
      
      {/* Loading spinner overlay */}
      {isRunning && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-70 rounded-lg">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}
    </div>
  );
};

export default PythonMessage;
