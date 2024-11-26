import React, { useEffect, useState } from 'react';
import useStore from '@store/store';
import { useTranslation, Trans } from 'react-i18next';

import PopupModal from '@components/PopupModal';
import CrossIcon from '@icon/CrossIcon';

const ApiPopup = () => {
  const { t } = useTranslation(['main', 'api']);

  const apiKey = useStore((state) => state.apiKey);
  const setApiKey = useStore((state) => state.setApiKey);
  const firstVisit = useStore((state) => state.firstVisit);
  const setFirstVisit = useStore((state) => state.setFirstVisit);

  // 永远不显示API Key输入弹窗
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  useEffect(() => {
    setFirstVisit(false);
  }, []);

  return <></>;
};

export default ApiPopup;
