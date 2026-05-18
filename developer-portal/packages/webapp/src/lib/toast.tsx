import React, { createContext, useCallback, useContext, useState } from "react";

type ToastMsg = { id: number; message: string; type: "success" | "error" };
type ToastCtx = { toast: (message: string, type?: "success" | "error") => void };

const Ctx = createContext<ToastCtx>({ toast: () => {} });

export function useToast() {
  return useContext(Ctx);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);

  const toast = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  }, []);

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-3 border-[1.5px] border-[#1B1034] text-sm font-medium max-w-sm ${
              t.type === "error" ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
