import React, { useState, useEffect } from 'react';
import { FaRegCopy, FaCheck } from "react-icons/fa";

const CLIOutMessage = ({ output }) => {
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
    navigator.clipboard.writeText(output).then(() => {
      setCopied(true);
    });
  };

  return (
    <div className="relative rounded-lg w-full bg-gray-800 p-4">
      {/* Header with CLI indicator and copy button */}
      <div className="flex justify-between items-center mb-2 text-gray-300 text-sm">
        <span>Command Line Output</span>
        <button 
          onClick={copyToClipboard}
          className="flex items-center space-x-1 hover:text-white transition-colors"
        >
          {copied ? (
            <FaCheck className="h-4 w-4 text-green-500" />
          ) : (
            <FaRegCopy className="h-4 w-4" />
          )}
          <span>{copied ? 'Copied!' : 'Copy output'}</span>
        </button>
      </div>
      
      {/* CLI output content */}
      <pre className="text-gray-100 overflow-x-auto p-2 font-mono text-sm bg-black rounded">
        <code>{output}</code>
      </pre>
    </div>
  );
};

export default CLIOutMessage;
