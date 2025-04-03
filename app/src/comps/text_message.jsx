import React, { Component } from 'react';

function TextMessage({ message }) {
    return ( 
        <div className="flex overflow-y-auto text-white break-words text-center justify-center items-center p-3 font-medium drop-shadow-xl">
            {message}
        </div>
    );
}

export default TextMessage;