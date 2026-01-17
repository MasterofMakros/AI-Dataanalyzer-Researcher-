'use client';

import { Dialog, DialogPanel } from '@headlessui/react';
import { motion } from 'framer-motion';
import { useEffect, useState, Fragment } from 'react';
import { RefreshCw, CheckCircle2, ArrowRight, Settings2 } from 'lucide-react';
import { toast } from 'sonner';
import Loader from '../ui/Loader';
import { cn } from '@/lib/utils';
import Select from '../ui/Select';

interface ProviderModels {
    chatModels: Array<{ id: string; name: string; key?: string }>;
    embeddingModels: Array<{ id: string; name: string; key?: string }>;
}

const OnboardingWizard = () => {
    const [step, setStep] = useState(1);
    const [isOpen, setIsOpen] = useState(false);
    const [isChecking, setIsChecking] = useState(true);
    const [isLoading, setIsLoading] = useState(false);

    // Form State
    const [ollamaUrl, setOllamaUrl] = useState('http://host.docker.internal:11434');
    const [models, setModels] = useState<ProviderModels>({ chatModels: [], embeddingModels: [] });
    const [selectedChatModel, setSelectedChatModel] = useState('');
    const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState('');

    // 1. Check if Setup is Needed
    useEffect(() => {
        const checkConfig = async () => {
            try {
                const res = await fetch('/api/providers');
                const data = await res.json();

                // If no providers or no models configured, show wizard
                const providers = data.providers || [];
                const hasChat = providers.some((p: any) => p.chatModels && p.chatModels.length > 0);
                const hasEmbedding = providers.some((p: any) => p.embeddingModels && p.embeddingModels.length > 0);

                if (!hasChat || !hasEmbedding) {
                    setIsOpen(true);
                }
            } catch (err) {
                console.error("Config check failed", err);
                setIsOpen(true); // Assume setup needed on error
            } finally {
                setIsChecking(false);
            }
        };

        checkConfig();
    }, []);

    // Action: Connect to Ollama
    const handleConnect = async () => {
        setIsLoading(true);
        try {
            // ... (rest of logic)
            const res = await fetch(`/api/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fields: {
                        modelProviders: {
                            ollama: {
                                baseUrl: ollamaUrl,
                                is_active: true // Ensure it's active
                            }
                        }
                    }
                })
            });

            if (!res.ok) throw new Error('Failed to update configuration');

            // 2. Fetch Models
            const modelsRes = await fetch('/api/providers/ollama/models');
            if (!modelsRes.ok) throw new Error('Failed to fetch models from Ollama');

            const modelsData = await modelsRes.json();
            setModels(modelsData);

            if (modelsData.chatModels?.length > 0) setSelectedChatModel(modelsData.chatModels[0].id || modelsData.chatModels[0].name);
            if (modelsData.embeddingModels?.length > 0) setSelectedEmbeddingModel(modelsData.embeddingModels[0].id || modelsData.embeddingModels[0].name);

            setStep(2);
            toast.success('Connected to Ollama!');

        } catch (err: any) {
            toast.error('Connection failed: ' + err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Action: Save Models
    const handleSave = async () => {
        setIsLoading(true);
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fields: {
                        modelProviders: {
                            ollama: {
                                chatModel: selectedChatModel,
                                embeddingModel: selectedEmbeddingModel
                            }
                        }
                    }
                })
            });

            // Force re-check or reload to apply
            window.location.reload();
        } catch (err: any) {
            toast.error("Failed to save models: " + err.message);
            setIsLoading(false);
        }
    };

    // if (isChecking) return null;

    return (
        <Dialog open={isOpen} onClose={() => { }} className="relative z-[100]">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />

            <div className="fixed inset-0 flex items-center justify-center p-4">
                <DialogPanel className="w-full max-w-md bg-light-primary dark:bg-dark-primary border border-light-200 dark:border-dark-200 rounded-2xl shadow-xl p-6">
                    <div className="space-y-6">

                        {/* Header */}
                        <div className="text-center space-y-2">
                            <div className="mx-auto w-12 h-12 bg-black dark:bg-white rounded-xl flex items-center justify-center mb-4">
                                <Settings2 className="text-white dark:text-black w-6 h-6" />
                            </div>
                            <h3 className="text-xl font-medium text-black dark:text-white">
                                {step === 1 ? 'Connect to AI' : 'Select Models'}
                            </h3>
                            <p className="text-sm text-black/60 dark:text-white/60">
                                {step === 1 ? 'Enter your Ollama URL to get started.' : 'Choose models for chat and embeddings.'}
                            </p>
                        </div>

                        {/* Step 1: Connect */}
                        {step === 1 && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-black/70 dark:text-white/70 uppercase">Ollama URL</label>
                                    <input
                                        type="text"
                                        value={ollamaUrl}
                                        onChange={(e) => setOllamaUrl(e.target.value)}
                                        className="w-full bg-light-secondary dark:bg-dark-secondary border border-light-200 dark:border-dark-200 rounded-lg px-3 py-2 text-sm focus:ring-2 ring-black/5 dark:ring-white/5 outline-none"
                                        placeholder="http://localhost:11434"
                                    />
                                </div>
                                <button
                                    onClick={handleConnect}
                                    disabled={isLoading}
                                    className="w-full bg-black dark:bg-white text-white dark:text-black font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                                >
                                    {isLoading ? <Loader /> : <>Connect <ArrowRight size={16} /></>}
                                </button>
                                <p className="text-xs text-center text-black/40 dark:text-white/40">
                                    Default: http://host.docker.internal:11434
                                </p>
                            </div>
                        )}

                        {/* Step 2: Select Models */}
                        {step === 2 && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-black/70 dark:text-white/70 uppercase">Chat Model</label>
                                    <Select
                                        value={selectedChatModel}
                                        onChange={(e) => setSelectedChatModel(e.target.value)}
                                        options={models.chatModels.map(m => ({ label: m.name, value: m.id }))}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-medium text-black/70 dark:text-white/70 uppercase">Embedding Model</label>
                                    <Select
                                        value={selectedEmbeddingModel}
                                        onChange={(e) => setSelectedEmbeddingModel(e.target.value)}
                                        options={models.embeddingModels.map(m => ({ label: m.name, value: m.id }))}
                                    />
                                </div>
                                <button
                                    onClick={handleSave}
                                    disabled={isLoading}
                                    className="w-full bg-black dark:bg-white text-white dark:text-black font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                                >
                                    {isLoading ? <Loader /> : <>Complete Setup <CheckCircle2 size={16} /></>}
                                </button>
                            </div>
                        )}

                    </div>
                </DialogPanel>
            </div>
        </Dialog>
    );
};

export default OnboardingWizard;
