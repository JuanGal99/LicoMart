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
  const data = error.response?.data;
  const isCsrf =
    error.response?.status === 403 &&
    (typeof data === "string"
      ? data.includes("CSRF")
      : data?.detail?.includes?.("CSRF"));
  if (isCsrf && !(error.config as Record<string, unknown>)._retry) {
    (error.config as Record<string, unknown>)._retry = true;
    await api.get("/usuarios/csrf/");
    return api(error.config);
  }
  return Promise.reject(error);
});

export default api;
