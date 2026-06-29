import { initializeApp, getApps, getApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  projectId: process.env.NEXT_PUBLIC_FIRESTORE_PROJECT_ID,
  apiKey: "dummy-api-key",
  authDomain: "dummy-auth-domain",
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const db = getFirestore(app);
