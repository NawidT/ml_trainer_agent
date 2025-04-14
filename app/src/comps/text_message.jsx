import React from 'react';

function TextMessage({ message, sender }) {
    return ( 
        <div className={`flex w-full overflow-y-auto text-white text-left justify-start items-start p-3 font-mono rounded-md bg-opacity-80 border-cyan-400 ${
          sender === 'user' ? 'bg-gray-500' : 'bg-black'
        }`}>
            <div className="w-full text-left">
                <div className="flex w-full items-start justify-start mb-1">
                    <div className="h-3 w-3 rounded-full bg-red-500 mr-1"></div>
                    <div className="h-3 w-3 rounded-full bg-yellow-500 mr-1"></div>
                    <div className="h-3 w-3 rounded-full bg-green-500"></div>
                    <div className="ml-2 text-xs text-gray-300">{sender}@terminal</div>
                </div>
                <div className="text-left whitespace-pre-wrap pl-1">
                    <span className="before:content-['$'] before:text-cyan-400 before:mr-2 before:font-bold">{message}</span>
                </div>
            </div>
        </div>
    );
}

export default TextMessage;