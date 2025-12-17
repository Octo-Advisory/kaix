import axios from 'axios';

// const BASE_URL = 'https://marsinfraix.marsbazaar.com';
const API_TOKEN = 'd3de1e0e4e25846:51fd8e403a19045';

export const getDataForSingleLayer = async (doctypeName, filters = null) => {
    try {
        let url = `/api/resource/${doctypeName}?fields=["*"]&limit=1000`;
        if (filters) {
            url += `&filters=${encodeURIComponent(JSON.stringify(filters))}`;
        }
        const headers = {
            'Authorization': `token ${API_TOKEN}`,
            'Content-Type': 'application/json'
        };
        const response = await axios.get(url, { headers });
        return response.data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
};


