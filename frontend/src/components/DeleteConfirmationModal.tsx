import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

interface HistoryItem {
  label: string;
  count: number;
}

interface DeleteImpact {
  history: boolean;
  items: HistoryItem[];
  detail: string;
}

interface Props {
  isOpen: boolean;
  title: string;
  message: string;
  impact?: DeleteImpact;
  onConfirm: (force: boolean) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function DeleteConfirmationModal({
  isOpen,
  title,
  message,
  impact,
  onConfirm,
  onCancel,
  isLoading
}: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Trash2 size={20} className="text-red-600" />
            {title}
          </h3>
          <button 
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          <p className="text-gray-600 mb-4">{message}</p>

          {impact && impact.history && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3 text-amber-800">
                <AlertTriangle className="shrink-0 mt-0.5" size={18} />
                <div className="text-sm">
                  <p className="font-bold mb-2">Advertencia de Historial:</p>
                  <p className="mb-3 text-amber-700">{impact.detail}</p>
                  <ul className="space-y-1 list-disc list-inside opacity-90">
                    {impact.items.map((item, idx) => (
                      <li key={idx}>
                        <span className="font-semibold">{item.count}</span> {item.label}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-xs font-medium uppercase tracking-wider opacity-75">
                    Al borrar, estos registros quedarán huérfanos o serán desvinculados.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <button
              onClick={() => onConfirm(!!impact?.history)}
              disabled={isLoading}
              className={`w-full py-2.5 px-4 rounded-lg font-semibold text-white transition-all
                ${impact?.history 
                  ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-100' 
                  : 'bg-red-600 hover:bg-red-700 shadow-red-100'
                } shadow-lg disabled:opacity-50 flex items-center justify-center gap-2`}
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {impact?.history ? 'Entiendo, borrar de todos modos' : 'Sí, eliminar definitivamente'}
                </>
              )}
            </button>
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
