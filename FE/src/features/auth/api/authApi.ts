import axios from 'axios';

// POST /user/logout
export const logoutUser = async () => {
    try {
        const response = await axios.post('/user/logout');
        return response.data;
    } catch (error) {
        console.error("Logout API failed", error);
        // Throwing so the caller knows it failed, though strict necessity depends on usage
        throw error;
    }
};
