import axios from "axios";

const api = axios.create({
  baseURL: "/",
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(undefined, async (error) => {
  if (error.response?.status === 403 && !error.config._retry) {
    error.config._retry = true;
    await api.get("/usuarios/csrf/");
    return api(error.config);
  }
  return Promise.reject(error);
});

export default api;
