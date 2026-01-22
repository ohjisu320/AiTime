import { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

// ✅ 우리가 방금 가져온 고급 UI 컴포넌트들
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

// 구글 아이콘 (SVG는 그대로 유지)
const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5 mr-2" aria-hidden="true">
    <path fill="#4285F4" d="M23.766 12.2764c0-.8847-.079-1.7371-.2269-2.5576H12v4.836h6.6268c-.2857 1.543-.377 2.0594-1.2657 3.2201v2.6665h4.0673c2.3807-2.1923 3.7544-5.4208 3.7544-9.1654z" />
    <path fill="#34A853" d="M12 24c3.24 0 5.957-1.074 7.942-2.906l-4.047-2.646c-1.164.78-2.529 1.154-3.895 1.154-2.997 0-5.556-1.956-6.495-4.665H1.405v3.016C3.439 21.996 7.42 24 12 24z" />
    <path fill="#FBBC05" d="M5.505 14.937c-.244-.725-.382-1.503-.382-2.308s.138-1.583.382-2.308V7.305H1.405C.507 9.088 0 11.085 0 13.264c0 2.18.507 4.176 1.405 5.959l4.1-3.016z" />
    <path fill="#EA4335" d="M12 4.757c1.739 0 3.298.6 4.524 1.77l3.39-3.39C17.952 1.206 15.235 0 12 0 7.42 0 3.439 2.004 1.405 5.305l4.1 3.016c.939-2.709 3.498-4.665 6.495-4.665z" />
  </svg>
);

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="w-full max-w-[420px] bg-white p-8 md:p-10 rounded-[20px] shadow-sm border border-gray-100">
      {/* 1. 헤더 */}
      <div className="mb-8 text-left">
        <h1 className="text-3xl font-bold text-[#2b3674] mb-2">Sign In</h1>
        <p className="text-gray-400 text-sm">
          Enter your email and password to sign in!
        </p>
      </div>

      {/* 2. 소셜 로그인 (Button 컴포넌트 사용) */}
      <Button variant="outline" className="w-full h-[50px] mb-6 bg-[#f4f7fe] border-none text-[#2b3674] font-medium hover:bg-gray-100">
        <GoogleIcon />
        Sign in with Google
      </Button>

      <div className="relative flex items-center justify-center mb-6">
        <div className="border-t border-gray-200 w-full"></div>
        <span className="bg-white px-3 text-gray-400 text-sm">or</span>
        <div className="border-t border-gray-200 w-full"></div>
      </div>

      {/* 3. 입력 폼 */}
      <form className="space-y-6">
        {/* 이메일 (Label, Input 컴포넌트 사용) */}
        <div className="space-y-2">
          <Label className="text-sm font-medium text-[#2b3674]">
            Email<span className="text-primary ml-1">*</span>
          </Label>
          <Input
            type="email"
            placeholder="mail@simmmple.com"
            className="h-[50px] rounded-[16px] border-[#e0e5f2] focus-visible:ring-primary"
          />
        </div>

        {/* 비밀번호 */}
        <div className="space-y-2">
          <Label className="text-sm font-medium text-[#2b3674]">
            Password<span className="text-primary ml-1">*</span>
          </Label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="Min. 8 characters"
              className="h-[50px] pr-10 rounded-[16px] border-[#e0e5f2] focus-visible:ring-primary"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {/* Remember Me (Checkbox 컴포넌트 사용) */}
        <div className="flex items-center justify-between mt-4 mb-6">
          <div className="flex items-center space-x-2">
            <Checkbox id="remember" className="data-[state=checked]:bg-primary data-[state=checked]:border-primary" />
            <Label htmlFor="remember" className="text-sm text-[#2b3674] font-normal cursor-pointer">
              Keep me logged in
            </Label>
          </div>
          <Link to="/forgot-password" className="text-sm text-primary font-medium hover:underline">
            Forgot Password?
          </Link>
        </div>

        {/* 로그인 버튼 (Button 컴포넌트 사용) */}
        <Button className="w-full h-[54px] rounded-[16px] text-sm font-bold shadow-lg shadow-primary/30">
          Sign In
        </Button>
      </form>

      <div className="mt-6 text-center text-sm text-[#2b3674]">
        Not registered yet?{" "}
        <Link to="/signup" className="text-primary font-bold hover:underline">
          Create an Account
        </Link>
      </div>
    </div>
  );
}