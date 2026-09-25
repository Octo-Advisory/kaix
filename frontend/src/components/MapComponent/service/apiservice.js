import axios from 'axios';

// const BASE_URL = 'https://marsinfraix.marsbazaar.com';
//const { data: adminToken } = useFrappeGetDoc("Mars Configurations", "admin_token")
  //const ADMIN_TOKEN = adminToken?.admin_token

export const getDataForSingleLayer = async (doctypeName, filters = null) => {
    try {
        let url = `/api/resource/${doctypeName}?fields=["*"]&limit=1000`;
        if (filters) {
            url += `&filters=${encodeURIComponent(JSON.stringify(filters))}`;
        }
        const headers = {
            'Authorization': `token d3de1e0e4e25846:8c3b173b4554288`,
            'Content-Type': 'application/json'
        };
        const response = await axios.get(url, { headers });
        return response.data;
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
};


