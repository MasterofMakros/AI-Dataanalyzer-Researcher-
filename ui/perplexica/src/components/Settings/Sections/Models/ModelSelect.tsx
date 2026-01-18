import Select from '@/components/ui/Select';
import { ConfigModelProvider } from '@/lib/config/types';
import { useChat } from '@/lib/hooks/useChat';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';

const ModelSelect = ({
  providers,
  type,
}: {
  providers: ConfigModelProvider[];
  type: 'chat' | 'embedding';
}) => {
  const [selectedModel, setSelectedModel] = useState<string>(
    type === 'chat'
      ? `${localStorage.getItem('chatModelProviderId')}/${localStorage.getItem('chatModelKey')}`
      : `${localStorage.getItem('embeddingModelProviderId')}/${localStorage.getItem('embeddingModelKey')}`,
  );
  const [loading, setLoading] = useState(false);
  const { setChatModelProvider, setEmbeddingModelProvider } = useChat();

  useEffect(() => {
    if (loading || !providers || providers.length === 0) return;

    if (!selectedModel || selectedModel === 'null/null') {
      // Find best default
    } else {
      const currentProviderId = selectedModel.split('/')[0];
      const currentModelKey = selectedModel.split('/').slice(1).join('/');

      const isValid = providers.some((p) =>
        p.id === currentProviderId &&
        (type === 'chat'
          ? p.chatModels.some((m) => m.key === currentModelKey)
          : p.embeddingModels.some((m) => m.key === currentModelKey))
      );
      if (isValid) return;
    }

    let bestModel = '';

    if (type === 'chat') {
      const ollama = providers.find((p) => p.id === 'ollama');
      if (ollama) {
        const qwen = ollama.chatModels.find((m) => m.name.toLowerCase().includes('qwen'));
        if (qwen) bestModel = `ollama/${qwen.key}`;
        else if (ollama.chatModels.length > 0) bestModel = `ollama/${ollama.chatModels[0].key}`;
      }
      if (!bestModel) {
        const firstWithModels = providers.find(p => p.chatModels.length > 0);
        if (firstWithModels) bestModel = `${firstWithModels.id}/${firstWithModels.chatModels[0].key}`;
      }
    } else {
      const ollama = providers.find((p) => p.id === 'ollama');
      if (ollama) {
        const qwen = ollama.embeddingModels.find((m) => m.name.toLowerCase().includes('qwen'));
        if (qwen) bestModel = `ollama/${qwen.key}`;
        else if (ollama.embeddingModels.length > 0) bestModel = `ollama/${ollama.embeddingModels[0].key}`;
      }
      if (!bestModel) {
        const firstWithModels = providers.find(p => p.embeddingModels.length > 0);
        if (firstWithModels) bestModel = `${firstWithModels.id}/${firstWithModels.embeddingModels[0].key}`;
      }
    }

    if (bestModel && bestModel !== selectedModel) {
      handleSave(bestModel);
    }
  }, [providers, type, selectedModel, loading]);

  const handleSave = async (newValue: string) => {
    setLoading(true);
    setSelectedModel(newValue);

    try {
      if (type === 'chat') {
        const providerId = newValue.split('/')[0];
        const modelKey = newValue.split('/').slice(1).join('/');

        localStorage.setItem('chatModelProviderId', providerId);
        localStorage.setItem('chatModelKey', modelKey);

        setChatModelProvider({
          providerId: providerId,
          key: modelKey,
        });
      } else {
        const providerId = newValue.split('/')[0];
        const modelKey = newValue.split('/').slice(1).join('/');

        localStorage.setItem('embeddingModelProviderId', providerId);
        localStorage.setItem('embeddingModelKey', modelKey);

        setEmbeddingModelProvider({
          providerId: providerId,
          key: modelKey,
        });
      }
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error('Failed to save configuration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-xl border border-light-200 bg-light-primary/80 p-4 lg:p-6 transition-colors dark:border-dark-200 dark:bg-dark-primary/80">
      <div className="space-y-3 lg:space-y-5">
        <div>
          <h4 className="text-sm lg:text-sm text-black dark:text-white">
            Select {type === 'chat' ? 'Chat Model' : 'Embedding Model'}
          </h4>
          <p className="text-[11px] lg:text-xs text-black/50 dark:text-white/50">
            {type === 'chat'
              ? 'Choose which model to use for generating responses'
              : 'Choose which model to use for generating embeddings'}
          </p>
        </div>
        <Select
          value={selectedModel}
          onChange={(event) => handleSave(event.target.value)}
          options={
            type === 'chat'
              ? providers.flatMap((provider) =>
                provider.chatModels
                  .filter((m) => !m.name.toLowerCase().includes('embed'))
                  .map((model) => ({
                    value: `${provider.id}/${model.key}`,
                    label: `${provider.name} - ${model.name}`,
                  })),
              )
              : providers.flatMap((provider) =>
                provider.embeddingModels.map((model) => ({
                  value: `${provider.id}/${model.key}`,
                  label: `${provider.name} - ${model.name}`,
                })),
              )
          }
          className="!text-xs lg:!text-[13px]"
          loading={loading}
          disabled={loading}
        />
      </div>
    </section>
  );
};

export default ModelSelect;
