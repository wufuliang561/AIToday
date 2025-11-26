import axios from 'axios';

const isServer = typeof window === 'undefined';
const API_BASE_URL = isServer
    ? (process.env.INTERNAL_API_URL || "http://backend:8000/api/v1")
    : (process.env.NEXT_PUBLIC_API_URL || "http://192.210.150.82/api/v1");

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000, // 10 seconds timeout
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for logging
// apiClient.interceptors.request.use(
//     (config) => {
//         console.log(`[Axios Request] ${config.method?.toUpperCase()} ${config.url}`);
//         return config;
//     },
//     (error) => {
//         console.error('[Axios Request Error]', error);
//         return Promise.reject(error);
//     }
// );

// Response interceptor for logging
// apiClient.interceptors.response.use(
//     (response) => {
//         console.log(`[Axios Response] ${response.status} ${response.config.url}`);
//         return response;
//     },
//     (error) => {
//         if (error.response) {
//             // The request was made and the server responded with a status code
//             // that falls out of the range of 2xx
//             console.error(`[Axios Response Error] ${error.response.status} ${error.config.url}`, error.response.data);
//         } else if (error.request) {
//             // The request was made but no response was received
//             console.error('[Axios No Response]', error.request);
//         } else {
//             // Something happened in setting up the request that triggered an Error
//             console.error('[Axios Error]', error.message);
//         }
//         return Promise.reject(error);
//     }
// );

export default apiClient;
