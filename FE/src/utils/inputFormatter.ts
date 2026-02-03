export const formatBirthdate = (val: string) => {
    const num = val.replace(/[^0-9]/g, "");
    if (num.length <= 4) return num;
    if (num.length <= 6) return `${num.slice(0, 4)}.${num.slice(4)}`;
    return `${num.slice(0, 4)}.${num.slice(4, 6)}.${num.slice(6, 8)}`; // YYYY.MM.DD
};

export const formatPhone = (val: string) => {
    const num = val.replace(/[^0-9]/g, "");
    if (num.length <= 3) return num;
    if (num.length <= 7) return `${num.slice(0, 3)}-${num.slice(3)}`;
    return `${num.slice(0, 3)}-${num.slice(3, 7)}-${num.slice(7, 11)}`; // 010-1234-5678
};
