import React from 'react';
import useStore from '@store/store';
import { useTranslation } from 'react-i18next';
import { ChatInterface, MessageInterface } from '@type/chat';
import { getChatCompletion, getChatCompletionStream } from '@api/api';
import { limitMessageTokens, updateTotalTokenUsed } from '@utils/messageUtils';
import { _defaultChatConfig } from '@constants/chat';
import { officialAPIEndpoint } from '@constants/auth';

const useSubmit = () => {
  const { t, i18n } = useTranslation('api');
  const error = useStore((state) => state.error);
  const setError = useStore((state) => state.setError);
  const apiEndpoint = useStore((state) => state.apiEndpoint);
  const apiKey = useStore((state) => state.apiKey);
  const setGenerating = useStore((state) => state.setGenerating);
  const generating = useStore((state) => state.generating);
  const currentChatIndex = useStore((state) => state.currentChatIndex);
  const setChats = useStore((state) => state.setChats);

  const generateTitle = async (
    message: MessageInterface[]
  ): Promise<string> => {
    let data;
    try {
      if (!apiKey || apiKey.length === 0) {
        // official endpoint
        if (apiEndpoint === officialAPIEndpoint) {
          throw new Error(t('noApiKeyWarning') as string);
        }

        // other endpoints
        data = await getChatCompletion(
          useStore.getState().apiEndpoint,
          message,
          _defaultChatConfig
        );
      } else if (apiKey) {
        // own apikey
        data = await getChatCompletion(
          useStore.getState().apiEndpoint,
          message,
          _defaultChatConfig,
          apiKey
        );
      }
    } catch (error: unknown) {
      throw new Error(`Error generating title!\n${(error as Error).message}`);
    }
    return data.choices[0].message.content;
  };

  const handleSubmit = async () => {
    const chats = useStore.getState().chats;
    if (generating || !chats) return;

    const updatedChats: ChatInterface[] = JSON.parse(JSON.stringify(chats));

    updatedChats[currentChatIndex].messages.push({
      role: 'assistant',
      content: '',
    });

    setChats(updatedChats);
    setGenerating(true);
    // console.log(updatedChats[currentChatIndex]);
    try {
      let stream;
      if (chats[currentChatIndex].messages.length === 0)
        throw new Error('No messages submitted!');

      const messages = limitMessageTokens(
        chats[currentChatIndex].messages,
        chats[currentChatIndex].config.max_tokens,
        chats[currentChatIndex].config.model
      );
      if (messages.length === 0) throw new Error('Message exceed max token!');
      // console.log(messages)
      // no api key (free)
      if (!apiKey || apiKey.length === 0) {
        // official endpoint
        if (apiEndpoint === officialAPIEndpoint) {
          throw new Error(t('noApiKeyWarning') as string);
        }
        // other endpoints
        stream = await getChatCompletionStream(
          useStore.getState().apiEndpoint,
          messages[messages.length-1]['content'],
          currentChatIndex,
          chats[currentChatIndex].config
        );
      } else if (apiKey) {
        // own apikey
        console.log(messages)
        stream = await getChatCompletionStream(
          useStore.getState().apiEndpoint,
            messages[messages.length-1]['content'],
            chats.length-currentChatIndex-1,
          chats[currentChatIndex].config,
          apiKey
        );
      }
      // chats[currentChatIndex].messages.push({role: "assistant", content:"Hi im **Nigger**"});
      // setChats(chats)
      if (stream) {
        if (stream.locked)
          throw new Error(
            'Oops, the stream is locked right now. Please try again'
          );
        const reader = stream.getReader()
        const textDecoder = new TextDecoder()
        let buffer = ''; // 用于存储未完整的数据

        const parseSSEResponse = (data: string): string => {
          try {
            // 移除 "data: " 前缀
            const jsonStr = data.replace(/^data: /, '');
            // 解析JSON
            const parsed = JSON.parse(jsonStr);
            return parsed.text || '';
          } catch (error) {
            console.error('Error parsing SSE data:', error);
            return '';
          }
        };

        while(true){
          const {done, value} = await reader.read()
          if(done){
            break
          }
          
          // 解码新接收的数据
          const chunk = textDecoder.decode(value, { stream: true });
          buffer += chunk;
          
          // 按双换行符分割数据
          const parts = buffer.split('\n\n');
          // 保留最后一个可能不完整的部分
          buffer = parts.pop() || '';
          
          // 处理完整的数据块
          for (const part of parts) {
            if (part.trim().length > 0) {
              const text = parseSSEResponse(part);
              if (text) {
                const updatedChats: ChatInterface[] = JSON.parse(
                  JSON.stringify(useStore.getState().chats)
                );
                const updatedMessages = updatedChats[currentChatIndex].messages;
                updatedMessages[updatedMessages.length - 1].content += text;
                setChats(updatedChats);
              }
            }
          }
        }

        // 处理缓冲区中剩余的数据
        if (buffer.trim().length > 0) {
          const text = parseSSEResponse(buffer);
          if (text) {
            const updatedChats: ChatInterface[] = JSON.parse(
              JSON.stringify(useStore.getState().chats)
            );
            const updatedMessages = updatedChats[currentChatIndex].messages;
            updatedMessages[updatedMessages.length - 1].content += text;
            setChats(updatedChats);
          }
        }

        if (useStore.getState().generating) {
          await reader.cancel('Cancelled by user');
        } else {
          await reader.cancel('Generation completed');
        }
        reader.releaseLock();
        await stream.cancel();
      }

      // update tokens used in chatting
      const currChats = useStore.getState().chats;
      const countTotalTokens = useStore.getState().countTotalTokens;

      if (currChats && countTotalTokens) {
        const model = currChats[currentChatIndex].config.model;
        const messages = currChats[currentChatIndex].messages;
        updateTotalTokenUsed(
          model,
          messages.slice(0, -1),
          messages[messages.length - 1]
        );
      }

      // generate title for new chats
      if (
        useStore.getState().autoTitle &&
        currChats &&
        !currChats[currentChatIndex]?.titleSet
      ) {
        const messages_length = currChats[currentChatIndex].messages.length;
        const assistant_message =
          currChats[currentChatIndex].messages[messages_length - 1].content;
        const user_message =
          currChats[currentChatIndex].messages[messages_length - 2].content;

        const message: MessageInterface = {
          role: 'user',
          content: `Generate a title in less than 6 words for the following message (language: ${i18n.language}):\n"""\nUser: ${user_message}\nAssistant: ${assistant_message}\n"""`,
        };

        let title = (await generateTitle([message])).trim();
        if (title.startsWith('"') && title.endsWith('"')) {
          title = title.slice(1, -1);
        }
        const updatedChats: ChatInterface[] = JSON.parse(
          JSON.stringify(useStore.getState().chats)
        );
        updatedChats[currentChatIndex].title = title;
        updatedChats[currentChatIndex].titleSet = true;
        setChats(updatedChats);

        // update tokens used for generating title
        if (countTotalTokens) {
          const model = _defaultChatConfig.model;
          updateTotalTokenUsed(model, [message], {
            role: 'assistant',
            content: title,
          });
        }
      }
    } catch (e: unknown) {
      const err = (e as Error).message;
      console.log(err);
      setError(err);
    }
    setGenerating(false);
  };

  return { handleSubmit, error };
};

export default useSubmit;
