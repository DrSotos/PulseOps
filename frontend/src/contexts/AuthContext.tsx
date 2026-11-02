import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "../types";
import { api } from "../services/api";
import { realtimeStream } from "../services/sse";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("pulseops_token");
    if (!token) {
      setLoading(false);
      return;
    }

    api
      .getMe()
      .then((userData) => {
        setUser(userData);
        realtimeStream.connect();
      })
      .catch(() => {
        localStorage.removeItem("pulseops_token");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      realtimeStream.disconnect();
    };
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.login(email, password);
    localStorage.setItem("pulseops_token", res.access_token);
    setUser(res.user);
    realtimeStream.connect();
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const res = await api.register(email, password, fullName);
    localStorage.setItem("pulseops_token", res.access_token);
    setUser(res.user);
    realtimeStream.connect();
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      realtimeStream.disconnect();
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

