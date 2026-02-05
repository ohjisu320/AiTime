import { useState, useEffect } from 'react';

interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

export const usePWAInstall = () => {
    const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
    const [isInstallable, setIsInstallable] = useState(false);
    const [isIOS, setIsIOS] = useState(false);
    const [isStandalone, setIsStandalone] = useState(false);

    useEffect(() => {
        // iOS 감지
        const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;
        setIsIOS(isIOSDevice);

        // 이미 PWA로 실행 중인지 확인 (standalone 모드)
        const isInStandaloneMode =
            window.matchMedia('(display-mode: standalone)').matches ||
            (window.navigator as any).standalone === true;
        setIsStandalone(isInStandaloneMode);

        // beforeinstallprompt 이벤트 (Android/Chrome 지원)
        const handleBeforeInstallPrompt = (e: Event) => {
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            // Stash the event so it can be triggered later.
            setDeferredPrompt(e as BeforeInstallPromptEvent);
            setIsInstallable(true);
            console.log('👋 PWA Install Prompt captured!');
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

        // 앱이 설치되었을 때
        window.addEventListener('appinstalled', () => {
            console.log('🎉 PWA was installed');
            setIsInstallable(false);
            setDeferredPrompt(null);
        });

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        };
    }, []);

    const installPWA = async () => {
        if (!deferredPrompt) {
            return;
        }
        // Show the install prompt
        await deferredPrompt.prompt();
        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`User response to the install prompt: ${outcome}`);
        // We've used the prompt, and can't use it again, throw it away
        setDeferredPrompt(null);
        setIsInstallable(false);
    };

    return {
        isInstallable,
        installPWA,
        isIOS,
        isStandalone,
        // iOS에서는 수동 설치 안내가 필요
        showIOSInstallGuide: isIOS && !isStandalone
    };
};
