const GuideVideo = () => {
  return (
    <div className="flex-1 bg-black rounded-3xl min-h-[500px] overflow-hidden shadow-2xl relative group">
      <video
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay muted loop playsInline
        poster="https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?auto=format&fit=crop&q=60&w=800"
      >
        <source src="https://assets.mixkit.co/videos/preview/mixkit-mother-and-her-little-daughter-playing-in-a-field-34440-large.mp4" type="video/mp4" />
      </video>
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="absolute bottom-8 left-8 flex items-center gap-3">
        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
        <span className="text-white text-lg font-bold tracking-wide">AiTime Guide</span>
      </div>
    </div>
  );
};

export default GuideVideo;