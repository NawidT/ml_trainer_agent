import React from 'react';
import TextMessage from './text_message';
import CLIOutMessage from './cliout_message';
import PythonMessage from './python_message';

const BaseAgentColumn = ({ title, messages }) => {
  return (
    <div className="flex flex-col h-full w-1/3 border-r border-gray-300">
      <div className="bg-gray-800 text-white p-4 text-center font-bold">
        {title}
      </div>
      <div className="flex-1 overflow-y-auto w-full flex flex-col items-center my-2 space-y-4">
        <div className="flex flex-col w-full py-2 items-center rounded-lg">
          {messages.length > 0 && messages.map((message, index) => (
            <div 
              key={index} 
              className={`flex w-11/12 min-h-[60px] justify-center align-center rounded-lg border-blue-500 border-2 mb-3 ${
                message.role === 'ai' ? 'bg-pink-800' : 'bg-black'
              }`}
            >
              {message.type === 'text' ? (
                <TextMessage message={message.content} sender={message.role} />
              ) : message.type === 'cli' ? (
                <CLIOutMessage output={message.content} />
              ) : (
                <PythonMessage code={message.content} isRunning={false} />
              )}
            </div>
          ))}
          {messages.length === 0 && (
            <div className="flex flex-col justify-center items-center text-gray-500">
              No messages yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BaseAgentColumn; 